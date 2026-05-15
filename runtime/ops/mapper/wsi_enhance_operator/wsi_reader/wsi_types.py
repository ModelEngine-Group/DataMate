from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np


class WSIFormat:
    OPENS = "openslide"


@dataclass
class WSIReaderConfig:
    format: str = WSIFormat.OPENS
    cache_size: int = 1024
    enable_lazy_loading: bool = True
    max_workers: int = 4


@dataclass
class SlideInfo:
    name: str
    path: str
    width: int
    height: int
    mpp_x: float = 0.0
    mpp_y: float = 0.0
    levels: int = 1
    format: str = WSIFormat.OPENS
    vendor: Optional[str] = None
    magnification: Optional[float] = None
    tile_count: Optional[int] = None
    file_size_bytes: Optional[int] = None

    def get_dimensions(self) -> Tuple[int, int]:
        return self.width, self.height


@dataclass
class PatchInfo:
    x: int
    y: int
    width: int
    height: int
    level: int
    data: np.ndarray
    source: str = "level_0"

    def get_position(self) -> Tuple[int, int]:
        return self.x, self.y

    def get_size(self) -> Tuple[int, int]:
        return self.width, self.height


@dataclass(frozen=True)
class Coordinate:
    x: int
    y: int
