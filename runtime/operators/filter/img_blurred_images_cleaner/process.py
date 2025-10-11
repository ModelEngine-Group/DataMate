# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description:
Create: 2025/01/17
"""
import time

import logging as logger
from typing import Dict, Any

import cv2
import numpy as np


from data_platform.common.utils import bytes_transform
from data_platform.core.base_op import Filter


class ImgBlurredImagesCleaner(Filter):
    """过滤模糊度低于阈值的图片插件"""

    def __init__(self, *args, **kwargs):
        super(ImgBlurredImagesCleaner, self).__init__(*args, **kwargs)
        # 设置模糊度阈值
        self._blurred_threshold = kwargs.get("blurredThreshold", 1000)

    def execute(self, sample: Dict[str, Any]):
        start = time.time()
        img_bytes = sample[self.data_key]
        file_name = sample[self.filename_key]
        file_type = "." + sample[self.filetype_key]
        if img_bytes:
            data = bytes_transform.bytes_to_numpy(img_bytes)
            blurred_images = self._blurred_images_filter(data, file_name)
            sample[self.data_key] = bytes_transform.numpy_to_bytes(blurred_images, file_type)
        logger.info("fileName: %s, method: ImagesBlurredCleaner costs %.6f s", file_name, time.time() - start)
        return sample

    def _blurred_images_filter(self, image, file_name):
        # 为方便与其他图片比较可以将图片resize到同一个大小
        img_resize = cv2.resize(image, (112, 112))
        # 将图片压缩为单通道的灰度图
        gray = cv2.cvtColor(img_resize, cv2.COLOR_BGR2GRAY)
        score = cv2.Laplacian(gray, cv2.CV_64F).var()
        if score <= self._blurred_threshold:
            logger.info("The image blur is %s, which exceeds the threshold of %s. %s is filtered out.", score,
                        self._blurred_threshold, file_name)
            return np.array([])
        return image
