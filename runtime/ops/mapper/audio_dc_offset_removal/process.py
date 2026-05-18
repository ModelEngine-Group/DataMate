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
            data, sr = sf.read(io.BytesIO(bytes(source)), always_2d=False)
        else:
            data, sr = sf.read(str(source), always_2d=False)
        return data, int(sr)
    except Exception as e:
        raise RuntimeError(f"读取音频失败（需要 soundfile）: error={e}") from e


def _dump_audio(data: "object", sr: int, fmt: str) -> bytes:
    try:
        import soundfile as sf  # type: ignore

        with io.BytesIO() as buf:
            sf.write(buf, data, int(sr), format=fmt.upper() if fmt else "WAV")
            return buf.getvalue()
    except Exception as e:
        raise RuntimeError(f"编码音频失败（需要 soundfile，fmt={fmt}）: {e}") from e


class AudioDcOffsetRemoval(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.out_format = "wav"

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

        data, sr = _load_audio(sample.get(self.data_key) or in_path)
        try:
            import numpy as np

            x = np.asarray(data, dtype=np.float32)
            if x.ndim > 1:
                x = x.mean(axis=1)
            y = x - float(np.mean(x)) if x.size else x
        except Exception as e:
            raise RuntimeError(f"处理失败（需要 numpy）: {e}") from e

        sample[self.data_key] = _dump_audio(y, sr, self.out_format)
        sample[self.text_key] = ""
        sample[self.target_type_key] = self.out_format
        sample[self.filetype_key] = "txt" if self.is_last_op else self.out_format

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioDcOffsetRemoval costs {time.time() - start:6f} s"
        )
        return sample
