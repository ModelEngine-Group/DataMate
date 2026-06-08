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
try:
    from .audio_skip import invalid_quality_reason, is_audio_sample, mark_skipped_sample
except ImportError:
    from audio_skip import invalid_quality_reason, is_audio_sample, mark_skipped_sample


DEFAULT_GTCRN_MODEL_PATH = "/models/AudioOperations/gtcrn/gtcrn.onnx"
DEFAULT_LID_MODEL_SOURCE = "/models/AudioOperations/lid/speechbrain_lang-id-voxlingua107-ecapa"
DEFAULT_LID_MODEL_SAVEDIR = "/models/AudioOperations/lid/_speechbrain_cache"
DEFAULT_ASR_MODEL_ROOT = "/models/AudioOperations/asr"


def _as_bool(v: object) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in {"1", "true", "yes", "y", "on"}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _audio_preprocessor_root() -> Path:
    return _repo_root() / "audio_preprocessor"


def _resolve_lid_model_source(value: str, ap_root: Path) -> str:
    raw = str(value or "").strip() or DEFAULT_LID_MODEL_SOURCE
    p = Path(raw).expanduser()
    if p.exists():
        return str(p)
    fallback = ap_root / "models" / "lid" / "speechbrain_lang-id-voxlingua107-ecapa"
    if fallback.exists():
        return str(fallback)
    return raw


def _ensure_sys_path(p: Path) -> None:
    import sys

    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)


def _safe_stem(sample: Dict[str, Any], filename_key: str) -> str:
    stem = Path(str(sample.get(filename_key) or "sample")).stem or "sample"
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in stem)


def _export_report_dir(sample: Dict[str, Any], export_path_key: str, filename_key: str) -> Path:
    export_root = Path(str(sample.get(export_path_key) or "")).expanduser()
    if not export_root:
        export_root = Path.cwd()
    if not export_root.is_absolute():
        export_root = (_repo_root() / export_root).resolve()
    return export_root / "audio_reports" / "asr_pipeline" / _safe_stem(sample, filename_key)


def _expand_dataset_placeholders(path_value: str, sample: Dict[str, Any] | None = None) -> str:
    value = str(path_value or "").strip()
    if sample:
        dataset_id = str(sample.get("dataset_id") or "").strip()
        if dataset_id:
            value = value.replace("{dataset_id}", dataset_id).replace("${dataset_id}", dataset_id)
            value = value.replace("{datasetId}", dataset_id).replace("${datasetId}", dataset_id)
    return value


def _resolve_optional_path(path_value: str, sample: Dict[str, Any] | None = None) -> Path:
    path_value = _expand_dataset_placeholders(path_value, sample)
    value = str(path_value or "").strip()
    if not value:
        return Path()
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = (_repo_root() / p).resolve()
    return p


def _find_named_file(root: Path | None, names: tuple[str, ...]) -> Path | None:
    if root is None:
        return None
    if root.is_file():
        return root if root.name in names else None
    for name in names:
        p = root / name
        if p.exists() and p.is_file():
            return p
    for p in root.rglob("*"):
        if p.is_file() and p.name in names:
            return p
    return None


def _valid_file_path(path: Path | None) -> bool:
    return path is not None and str(path) not in {"", "."} and path.exists() and path.is_file()


class AudioAsrPipeline(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.do_denoise = _as_bool(kwargs.get("doDenoise", False))
        self.denoise_model_path = str(kwargs.get("denoiseModelPath", DEFAULT_GTCRN_MODEL_PATH)).strip()

        self.do_anomaly_filter = _as_bool(kwargs.get("doAnomalyFilter", True))
        self.min_dur = float(kwargs.get("minDur", 1.0))
        self.max_dur = float(kwargs.get("maxDur", 20000.0))
        self.silence_ratio_th = float(kwargs.get("silenceRatioTh", 0.8))
        self.silence_rms_ratio_th = float(kwargs.get("silenceRmsRatioTh", 0.05))

        self.lid_model_source = str(kwargs.get("lidModelSource", "")).strip()
        self.lid_max_seconds = float(kwargs.get("lidMaxSeconds", 3.0))

        self.max_segment_seconds = int(float(kwargs.get("maxSegmentSeconds", 120)))

        self.do_keyword_recall = _as_bool(kwargs.get("doKeywordRecall", False))
        self.reference_path = str(kwargs.get("referencePath", "")).strip()
        self.zh_keyword_path = str(kwargs.get("zhKeywordPath", "")).strip()
        self.en_keyword_path = str(kwargs.get("enKeywordPath", "")).strip()
        self.keep_keyword_details = _as_bool(kwargs.get("keepKeywordDetails", False))

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        quality_skip_reason = invalid_quality_reason(sample, self.ext_params_key)
        if quality_skip_reason:
            return mark_skipped_sample(
                sample,
                quality_skip_reason,
                self.__class__.__name__,
                self.text_key,
                self.data_key,
                self.filetype_key,
                self.target_type_key,
                self.ext_params_key,
            )

        if not is_audio_sample(sample, self.filepath_key, self.filetype_key, self.target_type_key, self.data_key):
            return mark_skipped_sample(
                sample,
                "non_audio_or_reference_file",
                self.__class__.__name__,
                self.text_key,
                self.data_key,
                self.filetype_key,
                self.target_type_key,
                self.ext_params_key,
            )

        ap_root = _audio_preprocessor_root()
        if not ap_root.exists():
            raise FileNotFoundError(f"audio_preprocessor 不存在: {ap_root}")
        _ensure_sys_path(_repo_root())

        asr_model_root = Path(DEFAULT_ASR_MODEL_ROOT).resolve()
        if not asr_model_root.exists():
            raise FileNotFoundError(f"ASR 模型根目录不存在: {asr_model_root}")

        in_path = Path(sample.get(self.filepath_key, "")).resolve()
        if not in_path.exists():
            raise FileNotFoundError(f"输入音频不存在: {in_path}")

        reference_path = _resolve_optional_path(self.reference_path, sample)
        if reference_path:
            if not reference_path.exists():
                logger.warning(f"参考资源路径不存在，将继续使用显式关键词参数: {reference_path}")
                reference_path = Path()

        # 用临时工作区隔离每个 sample，避免污染 audio_preprocessor 自身的 output_data
        with tempfile.TemporaryDirectory(prefix="dm_audio_asr_") as td:
            work = Path(td)
            input_dir = work / "input_data" / "audio_raw"
            out_norm = work / "output_data" / "normalization"
            out_denoise = work / "output_data" / "denoise"
            out_lid = work / "output_data" / "lid"
            out_split = work / "output_data" / "split"
            out_asr = work / "output_data" / "asr"
            out_validation = work / "output_data" / "validation"
            models_link = work / "models"
            src_link = work / "src"

            input_dir.mkdir(parents=True, exist_ok=True)
            out_norm.mkdir(parents=True, exist_ok=True)
            out_denoise.mkdir(parents=True, exist_ok=True)
            out_lid.mkdir(parents=True, exist_ok=True)
            out_split.mkdir(parents=True, exist_ok=True)
            out_asr.mkdir(parents=True, exist_ok=True)
            out_validation.mkdir(parents=True, exist_ok=True)
            if not models_link.exists():
                models_link.symlink_to(asr_model_root.parent, target_is_directory=True)
            if not src_link.exists():
                src_link.symlink_to(ap_root / "src", target_is_directory=True)

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
                model = Path(self.denoise_model_path or DEFAULT_GTCRN_MODEL_PATH).expanduser().resolve()
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
                if quality_list.exists():
                    quality_rows = [
                        json.loads(line)
                        for line in quality_list.read_text(encoding="utf-8", errors="ignore").splitlines()
                        if line.strip()
                    ]
                    if quality_rows:
                        quality = quality_rows[0]
                        ext = sample.get(self.ext_params_key, {})
                        if not isinstance(ext, dict):
                            ext = {"_raw": ext}
                        ext["audio_quality"] = {
                            "quality_flag": str(quality.get("quality_flag", "ok")),
                            "duration": quality.get("duration", 0),
                            "silence_ratio": quality.get("silence_ratio", 0),
                            "global_rms": quality.get("global_rms", 0),
                            "reason": str(quality.get("reason", "")),
                        }
                        sample[self.ext_params_key] = ext
                        if str(quality.get("quality_flag", "ok")).lower() == "invalid":
                            sample[self.text_key] = ""
                            sample[self.data_key] = b""
                            sample[self.filetype_key] = ""
                            sample[self.target_type_key] = ""
                            logger.info(
                                f"fileName: {sample.get(self.filename_key)}, method: AudioAsrPipeline skipped: "
                                f"invalid_audio_quality:{quality.get('reason', 'invalid_audio')}"
                            )
                            return sample

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
                    "cpu",
                    "--batch_size",
                    "1",
                    "--max_seconds",
                    str(self.lid_max_seconds),
                ]
                sys.argv += ["--model_source", _resolve_lid_model_source(self.lid_model_source, ap_root)]
                sys.argv += ["--model_savedir", DEFAULT_LID_MODEL_SAVEDIR]
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
            project_root_backup = getattr(_rm, "PROJECT_ROOT", None)
            try:
                _rm.PROJECT_ROOT = work
                sys.argv = [
                    sys.argv[0],
                    "--split_dir",
                    str(out_split),
                    "--asr_root",
                    str(out_asr),
                    "--device",
                    "cpu",
                ]
                cwd_backup = os.getcwd()
                os.chdir(work)
                rc = _rm.main()
                if rc != 0:
                    raise RuntimeError(f"recognize_monitor 失败，返回码: {rc}")
            finally:
                if project_root_backup is not None:
                    _rm.PROJECT_ROOT = project_root_backup
                os.chdir(cwd_backup)
                sys.argv = argv_backup

            merged = out_asr / "merged_text.txt"
            if not merged.exists():
                raise RuntimeError(f"ASR 合并结果不存在: {merged}")

            merged_lines = [
                line.strip()
                for line in merged.read_text(encoding="utf-8", errors="ignore").splitlines()
                if line.strip()
            ]
            transcript_parts = []
            for line in merged_lines:
                parts = line.split(maxsplit=1)
                transcript_parts.append(parts[1] if len(parts) > 1 else "")
            merged_text = "\n".join(part for part in transcript_parts if part)

            keyword_recall = None
            if self.do_keyword_recall:
                import sys

                from audio_preprocessor.src.pipeline import eval_keyword_recall as _kwr  # type: ignore

                extra = reference_path if reference_path else None
                zh_kw = _resolve_optional_path(self.zh_keyword_path, sample) if self.zh_keyword_path else Path()
                if not _valid_file_path(zh_kw):
                    zh_kw = _find_named_file(extra, ("zh_keyword.txt", "zh_keywords.txt")) or Path()
                en_kw = _resolve_optional_path(self.en_keyword_path, sample) if self.en_keyword_path else Path()
                if not _valid_file_path(en_kw):
                    en_kw = _find_named_file(extra, ("en_keyword.txt", "en_keywords.txt")) or Path()
                if _valid_file_path(zh_kw) and not zh_kw.is_absolute():
                    zh_kw = (_repo_root() / zh_kw).resolve()
                if _valid_file_path(en_kw) and not en_kw.is_absolute():
                    en_kw = (_repo_root() / en_kw).resolve()
                if not _valid_file_path(zh_kw) and not _valid_file_path(en_kw):
                    raise FileNotFoundError(
                        f"关键词文件不存在。zhKeywordPath={zh_kw or ''}, enKeywordPath={en_kw or ''}, "
                        f"referencePath={reference_path or ''}"
                    )

                persistent_validation = _export_report_dir(sample, self.export_path_key, self.filename_key)
                persistent_validation.mkdir(parents=True, exist_ok=True)

                argv_backup = sys.argv[:]
                try:
                    sys.argv = [
                        sys.argv[0],
                        "--zh_kw",
                        str(zh_kw),
                        "--en_kw",
                        str(en_kw),
                        "--hyp",
                        str(merged),
                        "--work_dir",
                        str(persistent_validation),
                    ]
                    rc = _kwr.main()
                    if rc != 0:
                        raise RuntimeError(f"eval_keyword_recall 失败，返回码: {rc}")
                finally:
                    sys.argv = argv_backup

                zh_kw_map = _kwr.read_kw_kaldi(zh_kw)
                en_kw_map = _kwr.read_kw_kaldi(en_kw)
                hyp_map = _kwr.read_kv_text(merged)
                zh_result = _kwr.compute_keyword_recall_per_lang(
                    zh_kw_map, hyp_map, "中文", use_substring_match=True
                )
                en_result = _kwr.compute_keyword_recall_per_lang(
                    en_kw_map, hyp_map, "英文", use_substring_match=False
                )
                keyword_recall = {
                    "zh": {
                        "recall": round(float(zh_result[0]), 6),
                        "used_utterances": int(zh_result[1]),
                        "total_intersection_utterances": int(zh_result[2]),
                    },
                    "en": {
                        "recall": round(float(en_result[0]), 6),
                        "used_utterances": int(en_result[1]),
                        "total_intersection_utterances": int(en_result[2]),
                    },
                    "artifacts": {
                        "zh_keyword": str(zh_kw),
                        "en_keyword": str(en_kw),
                        "report": str(persistent_validation / "keyword_recall.txt"),
                        "report_dir": str(persistent_validation),
                    },
                }
                if self.keep_keyword_details:
                    keyword_recall["details"] = {
                        "zh": zh_result[3],
                        "en": en_result[3],
                    }

            # 写回 sample
            sample[self.text_key] = merged_text
            sample[self.data_key] = b""
            sample[self.filetype_key] = "txt"
            sample[self.target_type_key] = "txt"

            ext = sample.get(self.ext_params_key, {})
            if not isinstance(ext, dict):
                ext = {"_raw": ext}
            ext["audio_asr"] = {
                "lang": lang,
                "steps": {
                    "normalization": True,
                    "denoise": self.do_denoise,
                    "anomaly_filter": self.do_anomaly_filter,
                    "lid": True,
                    "split": True,
                    "asr": True,
                    "merge": True,
                    "keyword_recall": self.do_keyword_recall,
                },
            }
            if reference_path:
                ext["audio_asr"]["reference"] = {
                    "path": str(reference_path),
                    "type": "file" if reference_path.is_file() else "directory",
                }
            if keyword_recall is not None:
                ext["audio_asr"]["keyword_recall"] = keyword_recall
            sample[self.ext_params_key] = ext

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioAsrPipeline costs {time.time() - start:6f} s"
        )
        return sample
