# -- encoding: utf-8 --

import io
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from loguru import logger

from datamate.core.base_op import Mapper
try:
    from .audio_skip import invalid_quality_reason, is_audio_sample, mark_skipped_sample
except ImportError:
    from audio_skip import invalid_quality_reason, is_audio_sample, mark_skipped_sample


def _prepend_env_path(name: str, value: Path) -> None:
    if not value.exists():
        return
    current = os.environ.get(name, "")
    parts = [p for p in current.split(os.pathsep) if p]
    value_s = str(value)
    if value_s not in parts:
        os.environ[name] = os.pathsep.join([value_s] + parts)


def _external_ffmpeg_bin() -> Optional[str]:
    ops_site = Path(os.environ.get("DATAMATE_OPS_SITE_PACKAGES", "/usr/local/lib/ops/site-packages"))
    ffmpeg_root = Path(os.environ.get("DATAMATE_FFMPEG_ROOT", str(ops_site / "ffmpeg")))
    ffmpeg_bin = ffmpeg_root / "bin" / "ffmpeg"
    ffmpeg_lib = ffmpeg_root / "lib"
    if ffmpeg_bin.exists():
        _prepend_env_path("PATH", ffmpeg_bin.parent)
        _prepend_env_path("LD_LIBRARY_PATH", ffmpeg_lib)
        return str(ffmpeg_bin)
    return shutil.which("ffmpeg") or shutil.which("avconv")


def _load_audio_backend() -> Tuple[Optional[object], Optional[object]]:
    ffmpeg_bin = _external_ffmpeg_bin()
    audiosegment = None
    sf = None
    try:
        from pydub import AudioSegment  # type: ignore
        if ffmpeg_bin:
            AudioSegment.converter = ffmpeg_bin
            AudioSegment.ffmpeg = ffmpeg_bin
        audiosegment = AudioSegment
    except Exception:
        audiosegment = None

    try:
        import soundfile as _sf  # type: ignore

        sf = _sf
    except Exception:
        sf = None

    return audiosegment, sf


def _convert_with_pydub(source: object, target_sr: int, channels: int, fmt: str) -> bytes:
    audiosegment, _ = _load_audio_backend()
    if audiosegment is None:
        raise RuntimeError("pydub 不可用，无法使用 pydub 转换")

    if isinstance(source, (bytes, bytearray)):
        audio = audiosegment.from_file(io.BytesIO(bytes(source)))
    else:
        audio = audiosegment.from_file(str(source))
    if target_sr and target_sr > 0:
        audio = audio.set_frame_rate(int(target_sr))
    if channels == 1:
        audio = audio.set_channels(1)
    elif channels == 2:
        audio = audio.set_channels(2)

    with io.BytesIO() as buf:
        audio.export(buf, format=fmt)
        return buf.getvalue()


def _convert_with_soundfile(source: object, target_sr: int, channels: int, fmt: str) -> bytes:
    _, sf = _load_audio_backend()
    if sf is None:
        raise RuntimeError("soundfile 不可用，无法使用 soundfile 转换")
    if fmt not in {"wav", "flac", "ogg"}:
        raise RuntimeError(f"当前环境无 pydub 时不支持转换到: {fmt}")

    if isinstance(source, (bytes, bytearray)):
        data, sr = sf.read(io.BytesIO(bytes(source)), always_2d=True)
    else:
        data, sr = sf.read(str(source), always_2d=True)

    if channels == 1 and data.shape[1] > 1:
        data = data.mean(axis=1, keepdims=True)
    elif channels == 2 and data.shape[1] == 1:
        data = data.repeat(2, axis=1)

    if target_sr and target_sr > 0 and int(sr) != int(target_sr):
        try:
            import numpy as np

            new_len = max(1, int(round(data.shape[0] * float(target_sr) / float(sr))))
            old_x = np.linspace(0.0, 1.0, num=data.shape[0], endpoint=False)
            new_x = np.linspace(0.0, 1.0, num=new_len, endpoint=False)
            channels_data = [
                np.interp(new_x, old_x, data[:, ch]).astype(np.float32)
                for ch in range(data.shape[1])
            ]
            data = np.stack(channels_data, axis=1)
            sr = int(target_sr)
        except Exception as e:
            raise RuntimeError(f"重采样失败（需要 numpy），src_sr={sr}, target_sr={target_sr}: {e}") from e

    with io.BytesIO() as buf:
        sf.write(buf, data, int(sr), format=fmt.upper())
        return buf.getvalue()


def _ext_from_sample(sample: Dict[str, Any], default_ext: str) -> str:
    target_type = str(sample.get("target_type") or "").strip().lower().lstrip(".")
    file_type = str(sample.get("fileType") or "").strip().lower().lstrip(".")
    return target_type or file_type or default_ext


class AudioFormatConvert(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_format = str(kwargs.get("targetFormat", "wav")).strip().lower().lstrip(".")
        self.sample_rate = int(float(kwargs.get("sampleRate", 16000)))
        self.channels = int(float(kwargs.get("channels", 1)))

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

        in_path = Path(sample.get(self.filepath_key, "")).resolve()
        source = sample.get(self.data_key) or in_path
        if not isinstance(source, (bytes, bytearray)) and not in_path.exists():
            raise FileNotFoundError(f"输入音频不存在: {in_path}")

        source_ext = _ext_from_sample(sample, in_path.suffix.lower().lstrip(".") or self.target_format)
        audiosegment, sf = _load_audio_backend()
        try:
            if audiosegment is not None:
                out_bytes = _convert_with_pydub(
                    source=source,
                    target_sr=self.sample_rate,
                    channels=self.channels,
                    fmt=self.target_format,
                )
            else:
                if sf is None:
                    raise RuntimeError("pydub/soundfile 均不可用，无法转换")
                out_bytes = _convert_with_soundfile(
                    source=source,
                    target_sr=self.sample_rate,
                    channels=self.channels,
                    fmt=self.target_format,
                )
        except Exception as e:
            if in_path.suffix.lower().lstrip(".") == self.target_format and not sample.get(self.data_key):
                out_bytes = in_path.read_bytes()
            else:
                raise e

        sample[self.data_key] = out_bytes
        sample[self.text_key] = ""
        sample[self.target_type_key] = self.target_format
        if self.is_last_op:
            sample[self.filetype_key] = "txt"
        else:
            sample[self.filetype_key] = self.target_format

        ext = sample.get(self.ext_params_key, {})
        if not isinstance(ext, dict):
            ext = {"_raw": ext}
        ext["audio_format_convert"] = {
            "format": self.target_format,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "source_ext": source_ext,
        }
        sample[self.ext_params_key] = ext

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioFormatConvert costs {time.time() - start:6f} s"
        )
        return sample
