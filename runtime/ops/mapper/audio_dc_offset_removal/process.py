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

        data, sr = sf.read(str(path), always_2d=False)
        return data, int(sr)
    except Exception as e:
        raise RuntimeError(f"读取音频失败（需要 soundfile）: {path}, error={e}") from e


def _save_audio(path: Path, data: "object", sr: int, fmt: str) -> None:
    try:
        import soundfile as sf  # type: ignore

        path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(path), data, int(sr), format=fmt.upper() if fmt else None)
    except Exception as e:
        raise RuntimeError(f"写入音频失败（需要 soundfile）: {path}, error={e}") from e


class AudioDcOffsetRemoval(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.out_format = str(kwargs.get("outFormat", "wav")).strip().lower().lstrip(".")
        self.overwrite = _as_bool(kwargs.get("overwrite", False))

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()

        in_path = Path(sample.get(self.filepath_key, "")).resolve()
        if not in_path.exists():
            raise FileNotFoundError(f"输入音频不存在: {in_path}")

        data, sr = _load_audio(in_path)
        try:
            import numpy as np

            x = np.asarray(data, dtype=np.float32)
            if x.ndim > 1:
                x = x.mean(axis=1)
            y = x - float(np.mean(x)) if x.size else x
        except Exception as e:
            raise RuntimeError(f"处理失败（需要 numpy）: {e}") from e

        export_dir = Path(os.path.abspath(str(sample.get(self.export_path_key, "."))))
        export_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(str(sample.get(self.filename_key, in_path.name))).stem
        out_path = export_dir / f"{stem}.{self.out_format}"
        if out_path.exists() and not self.overwrite:
            raise FileExistsError(f"输出文件已存在且未启用覆盖: {out_path}")

        _save_audio(out_path, y, sr, self.out_format)

        sample[self.filepath_key] = str(out_path.resolve())
        sample[self.filetype_key] = self.out_format
        sample[self.filename_key] = out_path.name
        try:
            sample[self.filesize_key] = str(out_path.stat().st_size)
        except Exception:
            pass
        sample[self.data_key] = b""
        if not sample.get(self.text_key):
            sample[self.text_key] = "processed"

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioDcOffsetRemoval costs {time.time() - start:6f} s"
        )
        return sample

