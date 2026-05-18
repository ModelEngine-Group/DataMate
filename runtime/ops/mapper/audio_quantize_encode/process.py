# -- encoding: utf-8 --

import io
import time
from pathlib import Path
from typing import Dict, Any, Tuple

from loguru import logger

from datamate.core.base_op import Mapper
try:
    from .audio_skip import invalid_quality_reason, is_audio_sample, mark_skipped_sample
except ImportError:
    from audio_skip import invalid_quality_reason, is_audio_sample, mark_skipped_sample



def _load_audio(source: object) -> Tuple["object", int]:
    try:
        import soundfile as sf  # type: ignore

        if isinstance(source, (bytes, bytearray)):
            data, sr = sf.read(io.BytesIO(bytes(source)), always_2d=True)
        else:
            data, sr = sf.read(str(source), always_2d=True)
        return data, int(sr)
    except Exception as e:
        raise RuntimeError(f"读取音频失败（需要 soundfile）: error={e}") from e


def _dump_wav_pcm(data: "object", sr: int, subtype: str) -> bytes:
    try:
        import soundfile as sf  # type: ignore

        with io.BytesIO() as buf:
            sf.write(buf, data, int(sr), format="WAV", subtype=subtype)
            return buf.getvalue()
    except Exception as e:
        raise RuntimeError(f"编码 WAV 失败（需要 soundfile，subtype={subtype}）: {e}") from e


def _resample_linear(data: "object", src_sr: int, tgt_sr: int) -> "object":
    if src_sr <= 0 or tgt_sr <= 0 or int(src_sr) == int(tgt_sr):
        return data
    try:
        import numpy as np

        x = np.asarray(data, dtype=np.float32)  # (T, C)
        if x.ndim != 2:
            x = x.reshape((-1, 1))
        new_len = max(1, int(round(x.shape[0] * float(tgt_sr) / float(src_sr))))
        old_x = np.linspace(0.0, 1.0, num=x.shape[0], endpoint=False)
        new_x = np.linspace(0.0, 1.0, num=new_len, endpoint=False)
        return np.stack(
            [np.interp(new_x, old_x, x[:, ch]).astype(np.float32) for ch in range(x.shape[1])],
            axis=1,
        )
    except Exception as e:
        raise RuntimeError(f"重采样失败（需要 numpy）: {e}") from e


class AudioQuantizeEncode(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sample_rate = int(float(kwargs.get("sampleRate", 16000)))
        self.bit_depth = int(float(kwargs.get("bitDepth", 16)))
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
        if not in_path.exists():
            raise FileNotFoundError(f"输入音频不存在: {in_path}")

        data, sr = _load_audio(sample.get(self.data_key) or in_path)  # (T, C)
        try:
            import numpy as np

            x = np.asarray(data, dtype=np.float32)
            if self.channels == 1 and x.shape[1] > 1:
                x = x.mean(axis=1, keepdims=True)
            elif self.channels == 2 and x.shape[1] == 1:
                x = x.repeat(2, axis=1)
            x = _resample_linear(x, sr, self.sample_rate) if self.sample_rate > 0 else x
            out_sr = int(self.sample_rate) if self.sample_rate > 0 else int(sr)
        except Exception as e:
            raise RuntimeError(f"预处理失败: {e}") from e

        subtype_map = {
            8: "PCM_U8",
            16: "PCM_16",
            24: "PCM_24",
            32: "PCM_32",
        }
        if self.bit_depth not in subtype_map:
            raise ValueError(f"不支持的 bitDepth: {self.bit_depth}，仅支持 8/16/24/32")

        sample[self.data_key] = _dump_wav_pcm(x, out_sr, subtype=subtype_map[self.bit_depth])
        sample[self.text_key] = ""
        sample[self.target_type_key] = "wav"
        sample[self.filetype_key] = "txt"

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioQuantizeEncode costs {time.time() - start:6f} s"
        )
        return sample
