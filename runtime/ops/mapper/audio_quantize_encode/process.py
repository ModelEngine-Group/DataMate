# -- encoding: utf-8 --

import os
import time
from pathlib import Path
from typing import Dict, Any, Tuple

from loguru import logger

from datamate.core.base_op import Mapper


def _as_bool(v: object) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in {"1", "true", "yes", "y", "on"}


def _load_audio(path: Path) -> Tuple["object", int]:
    try:
        import soundfile as sf  # type: ignore

        data, sr = sf.read(str(path), always_2d=True)  # (T, C)
        return data, int(sr)
    except Exception as e:
        raise RuntimeError(f"读取音频失败（需要 soundfile）: {path}, error={e}") from e


def _save_wav_pcm(path: Path, data: "object", sr: int, subtype: str) -> None:
    try:
        import soundfile as sf  # type: ignore

        path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(path), data, int(sr), format="WAV", subtype=subtype)
    except Exception as e:
        raise RuntimeError(f"写入 WAV 失败（需要 soundfile，subtype={subtype}）: {path}, error={e}") from e


def _resample_linear(data: "object", src_sr: int, tgt_sr: int) -> "object":
    if src_sr <= 0 or tgt_sr <= 0 or int(src_sr) == int(tgt_sr):
        return data
    try:
        import numpy as np
        import torch  # type: ignore

        x = np.asarray(data, dtype=np.float32)  # (T, C)
        if x.ndim != 2:
            x = x.reshape((-1, 1))
        # (1, C, T)
        xt = torch.from_numpy(x).transpose(0, 1).unsqueeze(0)
        new_len = int(round(xt.shape[-1] * float(tgt_sr) / float(src_sr)))
        yt = torch.nn.functional.interpolate(xt, size=new_len, mode="linear", align_corners=False)
        y = yt.squeeze(0).transpose(0, 1).cpu().numpy().astype(np.float32)
        return y
    except Exception as e:
        raise RuntimeError(f"重采样失败（需要 torch/numpy）: {e}") from e


class AudioQuantizeEncode(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sample_rate = int(float(kwargs.get("sampleRate", 16000)))
        self.bit_depth = int(float(kwargs.get("bitDepth", 16)))
        self.channels = int(float(kwargs.get("channels", 1)))
        self.overwrite = _as_bool(kwargs.get("overwrite", False))

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        in_path = Path(sample.get(self.filepath_key, "")).resolve()
        if not in_path.exists():
            raise FileNotFoundError(f"输入音频不存在: {in_path}")

        data, sr = _load_audio(in_path)  # (T, C)
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

        export_dir = Path(os.path.abspath(str(sample.get(self.export_path_key, "."))))
        export_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(str(sample.get(self.filename_key, in_path.name))).stem
        out_path = export_dir / f"{stem}.wav"
        if out_path.exists() and not self.overwrite:
            raise FileExistsError(f"输出文件已存在且未启用覆盖: {out_path}")

        _save_wav_pcm(out_path, x, out_sr, subtype=subtype_map[self.bit_depth])

        sample[self.filepath_key] = str(out_path.resolve())
        sample[self.filetype_key] = "wav"
        sample[self.filename_key] = out_path.name
        try:
            sample[self.filesize_key] = str(out_path.stat().st_size)
        except Exception:
            pass
        sample[self.data_key] = b""
        if not sample.get(self.text_key):
            sample[self.text_key] = "encoded"

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioQuantizeEncode costs {time.time() - start:6f} s"
        )
        return sample

