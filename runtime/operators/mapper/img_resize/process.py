# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description:
Create: 2025/01/16
"""
import time
from typing import List, Dict, Any

import logging as logger
import cv2

from data_platform.common.utils import bytes_transform
from data_platform.core.base_op import Mapper


class ImgResize(Mapper):
    def __init__(self, *args, **kwargs):
        super(ImgResize, self).__init__(*args, **kwargs)
        self._target_size = kwargs.get("targetSize", [256, 256])

    @classmethod
    def _img_resize(cls, data: List[float], target_size: List[int]) -> List[float]:
        """将图片缩放到指定尺寸大小"""
        target_width = max(min(target_size[0], 4096), 1)
        target_height = max(min(target_size[1], 4096), 1)
        resized_img = cv2.resize(data, (target_width, target_height), interpolation=cv2.INTER_AREA)
        return resized_img

    def execute(self, sample: Dict[str, Any]):
        start = time.time()
        file_name = sample[self.filename_key]
        file_type = "." + sample[self.filetype_key]
        img_bytes = sample[self.data_key]
        if img_bytes:
            data = bytes_transform.bytes_to_numpy(img_bytes)
            resized_img = self._img_resize(data, self._target_size)
            sample[self.data_key] = bytes_transform.numpy_to_bytes(resized_img, file_type)
            logger.info("fileName: %s, method: ImgResize costs %.6f s", file_name, time.time() - start)
        return sample
