# -- encoding: utf-8 --

import os
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from loguru import logger

from datamate.core.base_op import Mapper


def _as_bool(v: object) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in {"1", "true", "yes", "y", "on"}


def _safe_export_path(sample: Dict[str, Any], key: str, default: str = "") -> str:
    v = sample.get(key, default)
    if v is None:
        return default
    return str(v)


def _load_audio_backend() -> Tuple[Optional[object], Optional[object]]:
    """
    Returns:
      (AudioSegment, sf)
      - AudioSegment: pydub.AudioSegment if available
      - sf: soundfile module if available
    """
    audiosegment = None
    sf = None
    try:
        from pydub import AudioSegment  # type: ignore

        audiosegment = AudioSegment
    except Exception:
        audiosegment = None

    try:
        import soundfile as _sf  # type: ignore

        sf = _sf
    except Exception:
        sf = None

    return audiosegment, sf


def _convert_with_soundfile(
    src: Path, dst: Path, target_sr: int, channels: int, fmt: str, overwrite: bool
) -> None:
    audiosegment, sf = _load_audio_backend()
    _ = audiosegment
    if sf is None:
        raise RuntimeError("soundfile 不可用，无法使用 soundfile 转换")

    if dst.exists() and not overwrite:
        raise FileExistsError(f"输出文件已存在且未启用覆盖: {dst}")

    data, sr = sf.read(str(src), always_2d=True)  # (T, C)
    if channels == 1 and data.shape[1] > 1:
        data = data.mean(axis=1, keepdims=True)
    elif channels == 2 and data.shape[1] == 1:
        data = data.repeat(2, axis=1)

    if target_sr and target_sr > 0 and int(sr) != int(target_sr):
        try:
            import numpy as np
            import torch  # type: ignore

            x = torch.from_numpy(data.astype("float32")).transpose(0, 1).unsqueeze(0)  # (1,C,T)
            new_len = int(round(x.shape[-1] * float(target_sr) / float(sr)))
            y = torch.nn.functional.interpolate(x, size=new_len, mode="linear", align_corners=False)
            data = y.squeeze(0).transpose(0, 1).cpu().numpy().astype(np.float32)
            sr = int(target_sr)
        except Exception as e:
            raise RuntimeError(f"重采样失败（需要 torch/numpy 支持），src_sr={sr}, target_sr={target_sr}: {e}") from e

    dst.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(dst), data, int(sr), format=fmt.upper() if fmt else None)


def _convert_with_pydub(
    src: Path, dst: Path, target_sr: int, channels: int, fmt: str, overwrite: bool
) -> None:
    audiosegment, sf = _load_audio_backend()
    _ = sf
    if audiosegment is None:
        raise RuntimeError("pydub 不可用，无法使用 pydub 转换")

    if dst.exists() and not overwrite:
        raise FileExistsError(f"输出文件已存在且未启用覆盖: {dst}")

    audio = audiosegment.from_file(str(src))
    if target_sr and target_sr > 0:
        audio = audio.set_frame_rate(int(target_sr))
    if channels == 1:
        audio = audio.set_channels(1)
    elif channels == 2:
        audio = audio.set_channels(2)
    dst.parent.mkdir(parents=True, exist_ok=True)
    audio.export(str(dst), format=fmt)


class AudioFormatConvert(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_format = str(kwargs.get("targetFormat", "wav")).strip().lower().lstrip(".")
        self.sample_rate = int(float(kwargs.get("sampleRate", 16000)))
        self.channels = int(float(kwargs.get("channels", 1)))
        self.overwrite = _as_bool(kwargs.get("overwrite", False))

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()

        src_path = Path(_safe_export_path(sample, self.filepath_key, "")).resolve()
        if not src_path.exists():
            raise FileNotFoundError(f"输入音频不存在: {src_path}")

        export_dir = Path(os.path.abspath(_safe_export_path(sample, self.export_path_key, ".")))
        export_dir.mkdir(parents=True, exist_ok=True)

        in_stem = Path(_safe_export_path(sample, self.filename_key, src_path.name)).stem
        out_name = f"{in_stem}.{self.target_format}"
        out_path = export_dir / out_name

        audiosegment, sf = _load_audio_backend()
        try:
            if audiosegment is not None:
                _convert_with_pydub(
                    src=src_path,
                    dst=out_path,
                    target_sr=self.sample_rate,
                    channels=self.channels,
                    fmt=self.target_format,
                    overwrite=self.overwrite,
                )
            else:
                # soundfile 支持的格式较少，优先兜底 wav/flac/ogg 等
                if sf is None:
                    raise RuntimeError("pydub/soundfile 均不可用，无法转换")
                if self.target_format not in {"wav", "flac", "ogg"}:
                    raise RuntimeError(f"当前环境无 pydub 时不支持转换到: {self.target_format}")
                _convert_with_soundfile(
                    src=src_path,
                    dst=out_path,
                    target_sr=self.sample_rate,
                    channels=self.channels,
                    fmt=self.target_format,
                    overwrite=self.overwrite,
                )
        except Exception as e:
            # 尝试“同格式复制”作为保底（仅当 target_format 与输入一致）
            if src_path.suffix.lower().lstrip(".") == self.target_format:
                if out_path.exists() and not self.overwrite:
                    raise
                shutil.copy2(str(src_path), str(out_path))
            else:
                raise e

        # 更新 sample 指向新文件
        sample[self.filepath_key] = str(out_path.resolve())
        sample[self.filetype_key] = self.target_format
        sample[self.filename_key] = out_path.name
        try:
            sample[self.filesize_key] = str(out_path.stat().st_size)
        except Exception:
            pass

        # 避免 BaseOp 误判为空内容
        if not sample.get(self.text_key):
            sample[self.text_key] = "converted"
        sample[self.data_key] = b""

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioFormatConvert costs {time.time() - start:6f} s"
        )
        return sample

