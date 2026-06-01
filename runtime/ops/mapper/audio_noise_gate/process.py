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


class AudioNoiseGate(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.threshold_db = float(kwargs.get("thresholdDb", -45))
        self.frame_ms = float(kwargs.get("frameMs", 20))
        self.hop_ms = float(kwargs.get("hopMs", 10))
        self.floor_ratio = float(kwargs.get("floorRatio", 0.05))
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
            if x.size == 0:
                y = x
            else:
                peak = float(np.max(np.abs(x))) + 1e-12
                th = peak * (10.0 ** (float(self.threshold_db) / 20.0))
                frame_len = max(1, int(sr * self.frame_ms / 1000.0))
                hop = max(1, int(sr * self.hop_ms / 1000.0))
                y = x.copy()
                for st in range(0, len(x), hop):
                    ed = min(st + frame_len, len(x))
                    frame = x[st:ed]
                    rms = float(np.sqrt(np.mean(frame * frame) + 1e-12))
                    if rms < th:
                        y[st:ed] = y[st:ed] * float(self.floor_ratio)
                y = np.clip(y, -1.0, 1.0)
        except Exception as e:
            raise RuntimeError(f"处理失败（需要 numpy）: {e}") from e

        sample[self.data_key] = _dump_audio(y, sr, self.out_format)
        sample[self.text_key] = ""
        sample[self.target_type_key] = self.out_format
        sample[self.filetype_key] = "txt" if self.is_last_op else self.out_format

        logger.info(f"fileName: {sample.get(self.filename_key)}, method: AudioNoiseGate costs {time.time() - start:6f} s")
        return sample
