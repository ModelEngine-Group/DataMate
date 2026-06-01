# -- encoding: utf-8 --

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


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _audio_preprocessor_root() -> Path:
    return _repo_root()


class AudioGtcrnDenoise(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_path = str(kwargs.get("modelPath", "")).strip()

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

        package_root = _audio_preprocessor_root()

        in_path = Path(sample.get(self.filepath_key, "")).resolve()
        audio_bytes = sample.get(self.data_key)
        if not audio_bytes and not in_path.exists():
            raise FileNotFoundError(f"输入音频不存在: {in_path}")

        model = Path(self.model_path or DEFAULT_GTCRN_MODEL_PATH).expanduser()
        model = model.resolve()
        if not model.exists():
            raise FileNotFoundError(f"GTCRN ONNX 模型不存在: {model}")

        # 直接调用 audio_preprocessor 的工具函数，避免 subprocess 路径/环境差异
        import sys

        utils_dir = package_root / "helpers" / "utils"
        if str(utils_dir) not in sys.path:
            sys.path.insert(0, str(utils_dir))

        from gtcrn_denoise import OnnxGtcrnDenoiser, process_one  # type: ignore

        denoiser = OnnxGtcrnDenoiser(model)
        with tempfile.TemporaryDirectory(prefix="audio_gtcrn_denoise_") as tmpdir:
            if audio_bytes:
                in_path = Path(tmpdir) / "input.wav"
                in_path.write_bytes(bytes(audio_bytes))
            out_path = Path(tmpdir) / "denoised.wav"
            process_one(in_path, out_path, denoiser)
            sample[self.data_key] = out_path.read_bytes()

        sample[self.text_key] = ""
        sample[self.target_type_key] = "wav"
        sample[self.filetype_key] = "txt" if self.is_last_op else "wav"

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioGtcrnDenoise costs {time.time() - start:6f} s"
        )
        return sample
