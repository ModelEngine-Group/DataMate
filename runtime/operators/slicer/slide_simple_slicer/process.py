# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 医疗图片按坐标切片
Create: 2025/02/08 11:00
"""
import copy
import time
from typing import List, Tuple, Dict, Any

import itertools
from loguru import logger

from openslide import OpenSlide
import numpy as np

from data_platform.core.base_op import Slicer

from data_platform.common.utils import bytes_transform


class SimpleSlicer(Slicer):

    def __init__(self, *args, **kwargs):
        super(SimpleSlicer, self).__init__(*args, **kwargs)

        self._target_size = kwargs.get("sliceSize", [128, 128])
        self._overlap = kwargs.get("overlap", 0)
        self.last_ops = True

        if not isinstance(self._target_size, List):
            raise TypeError(f"<targetSize> received as {type(self._target_size)}, but expected list.")
        if len(self._target_size) != 2:
            raise ValueError(f"<targetSize> has {len(self._target_size)} elements, but expected 2.")
        if not all(isinstance(dim, int) for dim in self._target_size):
            raise TypeError(f"Elements in <targetSize> must be integers, but got {self._target_size}.")
        if not isinstance(self._overlap, (int, float)):
            raise TypeError(f"<overlap> received as {type(self._overlap)}, but expected int.")
        if self._overlap < 0 or self._overlap > 1:
            raise ValueError(
                f"<overlap> received an out of range value: {self._overlap}, "
                f"but (0 <= overlap <= 1) is expected."
            )

    def execute(self, sample: Dict[str, Any]) -> List[Dict]:
        start = time.time()

        slide: OpenSlide = OpenSlide(sample["filePath"])
        if not isinstance(slide, OpenSlide):
            logger.error("Not desired <Image.Image> object.")
        dimensions: tuple[int, int] = slide.dimensions

        target_size = self._target_size
        overlap = self._overlap

        patch_num = self.auto_simple_slicer(sample, slide, dimensions, target_size, overlap)
        sample["slice_num"] = patch_num

        file_name = sample[self.filename_key]
        logger.info("fileName: %s, method: CoordinateSlider costs %.6f s", file_name, time.time() - start)

        return [sample]

    def auto_simple_slicer(
            self,
            original_sample: Dict[str, Any],
            slide: OpenSlide,
            dimensions: Tuple[int, int],
            target_size: Tuple[int, int],
            overlap: float
    ) -> int:
        """
        自动根据给定规格切片原图像

        Return: 
            List[Content] 每个 content 都是一个 data 为 patch 的 content
        """
        stride_x, stride_y = map(lambda x: int(x * (1 - overlap)), target_size)
        w, h = target_size

        patch_no = 0
        for x, y in itertools.product(
                range(0, dimensions[0] - w + 1, stride_x),
                range(0, dimensions[1] - h + 1, stride_y)
        ):
            # 切片
            region = slide.read_region((x, y), 0, target_size)

            region_np = np.array(region.convert("RGB"))

            patch_sample = copy.deepcopy(original_sample)
            patch_sample[self.data_key] = bytes_transform.numpy_to_bytes(region_np, ".png")
            patch_no += 1
            self.save_patch_sample(patch_sample, patch_no, save_format="image")

        logger.info(f"One image sliced into pieces: {patch_no}")

        return patch_no
