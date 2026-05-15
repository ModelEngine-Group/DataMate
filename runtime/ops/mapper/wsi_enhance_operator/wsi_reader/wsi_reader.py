from __future__ import annotations

import ctypes
import os
from typing import Tuple

import numpy as np

OPENSLIDE_LIBRARY_CANDIDATES = [
    "/models/WSIEnhance/openslide/libopenslide.so.1",
    "/models/WSIEnhance/openslide/libopenslide.so",
]


def _preload_openslide() -> Exception | None:
    for candidate in OPENSLIDE_LIBRARY_CANDIDATES:
        if not os.path.exists(candidate):
            continue
        try:
            ctypes.CDLL(candidate, mode=ctypes.RTLD_GLOBAL)
            return None
        except Exception as exc:  # pragma: no cover
            last_error = exc
    return locals().get("last_error")


try:
    _OPENSLIDE_PRELOAD_ERROR = _preload_openslide()
    import openslide
except Exception as exc:  # pragma: no cover
    openslide = None
    _OPENSLIDE_IMPORT_ERROR = _OPENSLIDE_PRELOAD_ERROR or exc
else:
    _OPENSLIDE_IMPORT_ERROR = None

try:
    from PIL import Image
except Exception as exc:  # pragma: no cover
    Image = None
    _PIL_IMPORT_ERROR = exc
else:
    _PIL_IMPORT_ERROR = None


RASTER_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
}


class WSIReader:
    def __init__(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input image not found: {file_path}")

        self.file_path = file_path
        self._slide = None
        self._image = None
        self._mode = "openslide"

        suffix = os.path.splitext(file_path)[1].lower()
        if openslide is not None:
            self._slide = openslide.OpenSlide(file_path)
            return

        if suffix in RASTER_EXTENSIONS and Image is not None:
            self._mode = "raster"
            self._image = np.array(Image.open(file_path).convert("RGB"), dtype=np.uint8)
            return

        raise ImportError(self._build_import_error_message(file_path))

    @staticmethod
    def _build_import_error_message(file_path: str) -> str:
        parts = [
            f"Unable to open WSI file: {file_path}",
            "OpenSlide shared library is not available in the runtime.",
        ]
        if _OPENSLIDE_IMPORT_ERROR is not None:
            parts.append(f"OpenSlide import error: {_OPENSLIDE_IMPORT_ERROR}")
        if Image is None and _PIL_IMPORT_ERROR is not None:
            parts.append(f"Pillow import error: {_PIL_IMPORT_ERROR}")
        parts.append(
            "Install the OpenSlide shared library for true WSI formats "
            "such as .svs/.ndpi, or use a standard raster image for fallback testing."
        )
        return " ".join(parts)

    @property
    def dimensions(self) -> Tuple[int, int]:
        if self._mode == "raster":
            height, width = self._image.shape[:2]
            return (int(width), int(height))
        return self._slide.dimensions

    @property
    def width(self) -> int:
        return int(self.dimensions[0])

    @property
    def height(self) -> int:
        return int(self.dimensions[1])

    @property
    def level_count(self) -> int:
        return 1 if self._mode == "raster" else int(self._slide.level_count)

    def get_thumbnail(self, max_size: Tuple[int, int] = (2048, 2048)) -> np.ndarray:
        if self._mode == "raster":
            image = Image.fromarray(self._image)
            image.thumbnail(max_size)
            return np.array(image, dtype=np.uint8)

        thumb = self._slide.get_thumbnail(max_size)
        arr = np.array(thumb)
        if arr.ndim == 2:
            arr = np.stack([arr, arr, arr], axis=-1)
        if arr.shape[-1] == 4:
            arr = arr[:, :, :3]
        return arr.astype(np.uint8, copy=False)

    def read_region(self, x: int, y: int, width: int, height: int, level: int = 0) -> np.ndarray:
        if self._mode == "raster":
            x0 = max(0, int(x))
            y0 = max(0, int(y))
            x1 = min(self.width, x0 + int(width))
            y1 = min(self.height, y0 + int(height))
            out = np.full((int(height), int(width), 3), 255, dtype=np.uint8)
            crop = self._image[y0:y1, x0:x1]
            if crop.size:
                out[0 : crop.shape[0], 0 : crop.shape[1]] = crop
            return out

        region = self._slide.read_region((int(x), int(y)), int(level), (int(width), int(height)))
        arr = np.array(region)
        if arr.shape[-1] == 4:
            arr = arr[:, :, :3]
        return arr.astype(np.uint8, copy=False)

    def close(self) -> None:
        if self._slide is not None:
            self._slide.close()
            self._slide = None

    def __enter__(self) -> "WSIReader":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
