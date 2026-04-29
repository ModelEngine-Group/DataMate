# -- encoding: utf-8 --

import os
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
    # .../DataMate/runtime/ops/mapper/<pkg>/process.py -> repo root
    return Path(__file__).resolve().parents[6]


def _audio_preprocessor_root() -> Path:
    return _repo_root() / "audio_preprocessor"


class AudioGtcrnDenoise(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_path = str(kwargs.get("modelPath", "")).strip()
        self.out_format = str(kwargs.get("outFormat", "wav")).strip().lower().lstrip(".")
        self.overwrite = _as_bool(kwargs.get("overwrite", False))

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()

        ap_root = _audio_preprocessor_root()
        if not ap_root.exists():
            raise FileNotFoundError(f"audio_preprocessor 不存在: {ap_root}")

        in_path = Path(sample.get(self.filepath_key, "")).resolve()
        if not in_path.exists():
            raise FileNotFoundError(f"输入音频不存在: {in_path}")

        export_dir = Path(os.path.abspath(str(sample.get(self.export_path_key, "."))))
        export_dir.mkdir(parents=True, exist_ok=True)

        stem = Path(str(sample.get(self.filename_key, in_path.name))).stem
        out_path = export_dir / f"{stem}.{self.out_format}"
        if out_path.exists() and not self.overwrite:
            raise FileExistsError(f"输出文件已存在且未启用覆盖: {out_path}")

        model = Path(self.model_path).expanduser() if self.model_path else (ap_root / "models" / "gtcrn" / "gtcrn.onnx")
        model = model.resolve()
        if not model.exists():
            raise FileNotFoundError(f"GTCRN ONNX 模型不存在: {model}")

        # 直接调用 audio_preprocessor 的工具函数，避免 subprocess 路径/环境差异
        import sys

        utils_dir = ap_root / "src" / "utils"
        if str(utils_dir) not in sys.path:
            sys.path.insert(0, str(utils_dir))

        from gtcrn_denoise import OnnxGtcrnDenoiser, process_one  # type: ignore

        denoiser = OnnxGtcrnDenoiser(model)
        process_one(in_path, out_path, denoiser)

        sample[self.filepath_key] = str(out_path.resolve())
        sample[self.filetype_key] = self.out_format
        sample[self.filename_key] = out_path.name
        try:
            sample[self.filesize_key] = str(out_path.stat().st_size)
        except Exception:
            pass
        sample[self.data_key] = b""
        if not sample.get(self.text_key):
            sample[self.text_key] = "denoised"

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioGtcrnDenoise costs {time.time() - start:6f} s"
        )
        return sample

