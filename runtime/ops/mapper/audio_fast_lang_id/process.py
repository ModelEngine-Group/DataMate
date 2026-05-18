# -- encoding: utf-8 --

import json
import re
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


DEFAULT_LID_MODEL_SOURCE = "/models/AudioOperations/lid/speechbrain_lang-id-voxlingua107-ecapa"
DEFAULT_LID_MODEL_SAVEDIR = "/models/AudioOperations/lid/_speechbrain_cache"


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _audio_preprocessor_root() -> Path:
    return _repo_root()


def _resolve_lid_model_source(value: str, package_root: Path) -> str:
    raw = str(value or "").strip() or DEFAULT_LID_MODEL_SOURCE
    p = Path(raw).expanduser()
    if p.exists():
        return str(p)
    fallback = package_root / "models" / "lid" / "speechbrain_lang-id-voxlingua107-ecapa"
    if fallback.exists():
        return str(fallback)
    return raw


def _audio_ext(sample: Dict[str, Any], default_ext: str = "wav") -> str:
    ext = str(sample.get("target_type") or sample.get("fileType") or default_ext).strip().lower().lstrip(".")
    return ext or default_ext


def _strip_lid_marker(stem: str) -> str:
    return re.sub(r"__lid_(zh|en)$", "", str(stem or "sample"))


def _mark_lid_filename(sample: Dict[str, Any], filename_key: str, lang: str, target_ext: str) -> None:
    file_name = str(sample.get(filename_key) or "").strip()
    stem = _strip_lid_marker(Path(file_name).stem if file_name else "sample")
    sample[filename_key] = f"{stem}__lid_{lang}.{target_ext}"


class AudioFastLangId(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_source = str(kwargs.get("modelSource", "")).strip()
        self.model_savedir = str(kwargs.get("modelSavedir", "")).strip()
        self.device = str(kwargs.get("device", "cpu")).strip()
        self.batch_size = int(float(kwargs.get("batchSize", 1)))
        self.max_seconds = float(kwargs.get("maxSeconds", 3.0))

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

        import sys

        package_root = _audio_preprocessor_root()
        utils_dir = package_root / "helpers" / "utils"
        if str(utils_dir) not in sys.path:
            sys.path.insert(0, str(utils_dir))

        import fast_lang_id  # type: ignore

        with tempfile.TemporaryDirectory(prefix="dm_audio_lid_") as td:
            work_dir = Path(td)
            data = sample.get(self.data_key)
            audio_bytes_for_export = b""
            if isinstance(data, (bytes, bytearray)) and data:
                audio_bytes_for_export = bytes(data)
                wav_path = work_dir / f"input.{_audio_ext(sample)}"
                wav_path.write_bytes(audio_bytes_for_export)
            else:
                wav_path = Path(sample.get(self.filepath_key, "")).resolve()
                if not wav_path.exists():
                    raise FileNotFoundError(f"输入音频不存在: {wav_path}")
                audio_bytes_for_export = wav_path.read_bytes()

            out_path = work_dir / "item_with_lang.list"
            in_list = work_dir / "single_item.list"
            in_list.write_text(
                json.dumps({"key": wav_path.stem, "wav": str(wav_path), "txt": ""}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            # 组装 args，直接复用其 main() 的 CLI 解析逻辑
            argv_backup = sys.argv[:]
            try:
                sys.argv = [
                    sys.argv[0],
                    "--input_list",
                    str(in_list),
                    "--output",
                    str(out_path),
                    "--device",
                    self.device,
                    "--batch_size",
                    str(max(1, self.batch_size)),
                    "--max_seconds",
                    str(self.max_seconds),
                ]
                model_source = _resolve_lid_model_source(self.model_source, package_root)
                model_savedir = self.model_savedir or DEFAULT_LID_MODEL_SAVEDIR
                sys.argv += ["--model_source", model_source, "--model_savedir", model_savedir]

                rc = fast_lang_id.main()
                if rc != 0:
                    raise RuntimeError(f"fast_lang_id 失败，返回码: {rc}")
            finally:
                sys.argv = argv_backup

            if not out_path.exists():
                raise RuntimeError(f"LID 输出不存在: {out_path}")
            lines = [line.strip() for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if not lines:
                raise RuntimeError(f"LID 输出为空: {out_path}")
            d = json.loads(lines[0])
            lang = str(d.get("lang", "en"))

        ext = sample.get(self.ext_params_key, {})
        if not isinstance(ext, dict):
            ext = {"_raw": ext}
        ext["audio_lid"] = {"lang": lang}
        sample[self.ext_params_key] = ext

        target_ext = _audio_ext(sample)
        if audio_bytes_for_export:
            sample[self.data_key] = audio_bytes_for_export
        sample[self.text_key] = ""
        if self.is_last_op:
            sample[self.filetype_key] = "txt"
            sample[self.target_type_key] = target_ext
        else:
            sample[self.filetype_key] = target_ext
            sample[self.target_type_key] = target_ext
        _mark_lid_filename(sample, self.filename_key, lang, target_ext)

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioFastLangId costs {time.time() - start:6f} s"
        )
        return sample
