# -- encoding: utf-8 --

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Dict, Any

from loguru import logger

from datamate.core.base_op import Mapper


def _as_bool(v: object) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in {"1", "true", "yes", "y", "on"}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[6]


def _audio_preprocessor_root() -> Path:
    return _repo_root() / "audio_preprocessor"


def _ensure_sys_path(p: Path) -> None:
    import sys

    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)


class AudioAsrPipeline(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.do_denoise = _as_bool(kwargs.get("doDenoise", False))
        self.denoise_model_path = str(kwargs.get("denoiseModelPath", "")).strip()

        self.do_anomaly_filter = _as_bool(kwargs.get("doAnomalyFilter", True))
        self.min_dur = float(kwargs.get("minDur", 1.0))
        self.max_dur = float(kwargs.get("maxDur", 20000.0))
        self.silence_ratio_th = float(kwargs.get("silenceRatioTh", 0.8))
        self.silence_rms_ratio_th = float(kwargs.get("silenceRmsRatioTh", 0.05))

        self.lid_model_source = str(kwargs.get("lidModelSource", "")).strip()
        self.lid_device = str(kwargs.get("lidDevice", "cpu")).strip()
        self.lid_max_seconds = float(kwargs.get("lidMaxSeconds", 3.0))

        self.max_segment_seconds = int(float(kwargs.get("maxSegmentSeconds", 120)))
        self.asr_device = str(kwargs.get("asrDevice", "auto")).strip()

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()

        ap_root = _audio_preprocessor_root()
        if not ap_root.exists():
            raise FileNotFoundError(f"audio_preprocessor 不存在: {ap_root}")

        in_path = Path(sample.get(self.filepath_key, "")).resolve()
        if not in_path.exists():
            raise FileNotFoundError(f"输入音频不存在: {in_path}")

        # 用临时工作区隔离每个 sample，避免污染 audio_preprocessor 自身的 output_data
        with tempfile.TemporaryDirectory(prefix="dm_audio_asr_") as td:
            work = Path(td)
            input_dir = work / "input_data" / "audio_raw"
            out_norm = work / "output_data" / "normalization"
            out_denoise = work / "output_data" / "denoise"
            out_lid = work / "output_data" / "lid"
            out_split = work / "output_data" / "split"
            out_asr = work / "output_data" / "asr"

            input_dir.mkdir(parents=True, exist_ok=True)
            out_norm.mkdir(parents=True, exist_ok=True)
            out_denoise.mkdir(parents=True, exist_ok=True)
            out_lid.mkdir(parents=True, exist_ok=True)
            out_split.mkdir(parents=True, exist_ok=True)
            out_asr.mkdir(parents=True, exist_ok=True)

            # 复制输入音频到 pipeline 输入目录
            src_name = in_path.name
            local_in = input_dir / src_name
            shutil.copy2(str(in_path), str(local_in))

            # 1) normalization（调用 audio_preprocessor 的 normalization.main，但用我们自己的 input/output_dir）
            _ensure_sys_path(ap_root / "scripts" / "audio_convert")
            _ensure_sys_path(ap_root / "src" / "utils")
            _ensure_sys_path(ap_root / "src" / "pipeline")

            import sys

            from audio_preprocessor.src.pipeline import normalization as _norm  # type: ignore

            argv_backup = sys.argv[:]
            try:
                sys.argv = [
                    sys.argv[0],
                    "--input_dir",
                    str(input_dir),
                    "--output_dir",
                    str(out_norm),
                    "--overwrite",
                ]
                rc = _norm.main()
                if rc != 0:
                    raise RuntimeError(f"normalization 失败，返回码: {rc}")
            finally:
                sys.argv = argv_backup

            # 归一化输出文件（按 stem）
            norm_candidates = sorted(out_norm.glob(f"{Path(src_name).stem}.*"))
            if not norm_candidates:
                # 兜底：取目录内第一个文件
                norm_candidates = sorted([p for p in out_norm.iterdir() if p.is_file()])
            if not norm_candidates:
                raise RuntimeError(f"normalization 未生成输出: {out_norm}")
            norm_file = norm_candidates[0]

            current_audio_dir = out_norm

            # 2) (可选) GTCRN denoise（直接复用工具类）
            if self.do_denoise:
                if not self.denoise_model_path:
                    raise ValueError("启用降噪时必须提供 denoiseModelPath（GTCRN onnx 绝对路径）")
                model = Path(self.denoise_model_path).expanduser().resolve()
                if not model.exists():
                    raise FileNotFoundError(f"GTCRN 模型不存在: {model}")

                _ensure_sys_path(ap_root / "src" / "utils")
                from audio_preprocessor.src.utils.gtcrn_denoise import OnnxGtcrnDenoiser, process_one  # type: ignore

                denoiser = OnnxGtcrnDenoiser(model)
                den_out = out_denoise / f"{norm_file.stem}.wav"
                process_one(norm_file, den_out, denoiser)
                current_audio_dir = out_denoise

            # 3) (可选) anomaly_filter（复用其模块 main，通过 argv 注入参数）
            quality_list = out_denoise / "item_with_quality.list"
            if self.do_anomaly_filter:
                from audio_preprocessor.src.pipeline import anomaly_filter as _af  # type: ignore

                argv_backup = sys.argv[:]
                try:
                    sys.argv = [
                        sys.argv[0],
                        "--audio_dir",
                        str(current_audio_dir),
                        "--output",
                        str(quality_list),
                        "--min_dur",
                        str(self.min_dur),
                        "--max_dur",
                        str(self.max_dur),
                        "--silence_ratio_th",
                        str(self.silence_ratio_th),
                        "--silence_rms_ratio_th",
                        str(self.silence_rms_ratio_th),
                    ]
                    rc = _af.main()
                    if rc != 0:
                        raise RuntimeError(f"anomaly_filter 失败，返回码: {rc}")
                finally:
                    sys.argv = argv_backup

            # 4) LID：fast_lang_id（用 input_list，保证只处理本文件）
            from audio_preprocessor.src.utils import fast_lang_id as _lid  # type: ignore

            lid_in_list = out_lid / "_single_item.list"
            lid_in_list.write_text(
                json.dumps({"key": norm_file.stem, "wav": str((current_audio_dir / norm_file.name).resolve()), "txt": ""}, ensure_ascii=False)
                + "\n",
                encoding="utf-8",
            )
            lid_out_list = out_lid / "item_with_lang.list"
            argv_backup = sys.argv[:]
            try:
                sys.argv = [
                    sys.argv[0],
                    "--input_list",
                    str(lid_in_list),
                    "--output",
                    str(lid_out_list),
                    "--device",
                    self.lid_device,
                    "--batch_size",
                    "1",
                    "--max_seconds",
                    str(self.lid_max_seconds),
                ]
                if self.lid_model_source:
                    sys.argv += ["--model_source", self.lid_model_source]
                rc = _lid.main()
                if rc != 0:
                    raise RuntimeError(f"fast_lang_id 失败，返回码: {rc}")
            finally:
                sys.argv = argv_backup

            lid_line = lid_out_list.read_text(encoding="utf-8").splitlines()[0].strip()
            lid_row = json.loads(lid_line)
            lang = str(lid_row.get("lang", "en"))

            # 5) split_and_tag
            from audio_preprocessor.src.pipeline import split_and_tag as _split  # type: ignore

            argv_backup = sys.argv[:]
            try:
                sys.argv = [
                    sys.argv[0],
                    "--input_dir",
                    str(current_audio_dir),
                    "--output_dir",
                    str(out_split),
                    "--list_file",
                    str(lid_out_list),
                    "--from_list",
                    "--max_seconds",
                    str(max(1, self.max_segment_seconds)),
                ]
                rc = _split.main()
                if rc != 0:
                    raise RuntimeError(f"split_and_tag 失败，返回码: {rc}")
            finally:
                sys.argv = argv_backup

            split_list = out_split / "item_with_lang.list"
            if not split_list.exists():
                raise RuntimeError(f"split 输出清单不存在: {split_list}")

            # 6) recognize_monitor
            from audio_preprocessor.src.pipeline import recognize_monitor as _rm  # type: ignore

            argv_backup = sys.argv[:]
            try:
                sys.argv = [
                    sys.argv[0],
                    "--split_dir",
                    str(out_split),
                    "--asr_root",
                    str(out_asr),
                    "--device",
                    self.asr_device,
                ]
                rc = _rm.main()
                if rc != 0:
                    raise RuntimeError(f"recognize_monitor 失败，返回码: {rc}")
            finally:
                sys.argv = argv_backup

            merged = out_asr / "merged_text.txt"
            if not merged.exists():
                raise RuntimeError(f"ASR 合并结果不存在: {merged}")

            merged_text = merged.read_text(encoding="utf-8", errors="ignore").strip()
            if not merged_text:
                merged_text = ""

            # 写回 sample
            sample[self.text_key] = merged_text
            sample[self.data_key] = b""

            ext = sample.get(self.ext_params_key, {})
            if not isinstance(ext, dict):
                ext = {"_raw": ext}
            ext["audio_asr"] = {
                "lang": lang,
                "artifacts": {
                    "work_dir": str(work),
                    "normalized_dir": str(out_norm),
                    "denoise_dir": str(out_denoise) if self.do_denoise else "",
                    "lid_list": str(lid_out_list),
                    "split_dir": str(out_split),
                    "asr_dir": str(out_asr),
                    "merged_text": str(merged),
                },
            }
            sample[self.ext_params_key] = ext

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioAsrPipeline costs {time.time() - start:6f} s"
        )
        return sample

