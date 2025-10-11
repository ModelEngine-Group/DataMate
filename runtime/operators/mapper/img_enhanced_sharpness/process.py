# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 图片锐度自适应增强
Version:
Create: 2025/01/13
"""

import time

import logging as logger
from typing import Dict, Any

import cv2
import numpy as np

from data_platform.common.utils import bytes_transform
from data_platform.core.base_op import Mapper


class ImgSharpness(Mapper):
    """图片锐度自适应增强"""

    def __init__(self, *args, **kwargs):
        super(ImgSharpness, self).__init__(*args, **kwargs)
        # 自适应增强参数
        self.factor_threshold = 1.1  # 图片增强因子下限(不作为参数传入)。
        self.standard_mean = 100  # 图片增强后的平均锐度(不作为参数传入)。
        self.kernel = self._init_kernel()
        self.eps = 1  # 小值，计算图像锐度增强因子的时候，防止全黑图片导致的除零错(不作为参数传入)。

    @classmethod
    def _init_kernel(cls):
        kernel = np.array([[1, 1, 1],
                           [1, 5, 1],
                           [1, 1, 1]])
        # 对卷积核进行归一化
        kernel = kernel / np.sum(kernel)
        return kernel

    def enhance_sharpness(self, image_data: np.ndarray, file_name):
        """锐度自适应增强方法"""

        # 打开图像并转换为灰度图像
        image_gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
        sharpness = np.abs(cv2.Laplacian(image_gray, cv2.CV_8U)).mean()
        sharpness_factor = self.standard_mean / (sharpness + self.eps)

        # 图片锐度较高，不需要增强锐度
        if sharpness_factor <= 1:
            logger.info("fileName: %s, method: ImgSharpness not need enhancement", file_name)
            return image_data

        filtered_img = cv2.filter2D(image_data, -1, self.kernel)
        cv2.addWeighted(image_data, sharpness_factor, filtered_img, 1.0 - sharpness_factor, 0, dst=image_data)
        return image_data

    def execute(self, sample: Dict[str, Any]):
        start = time.time()
        img_bytes = sample[self.data_key]
        file_name = sample[self.filename_key]
        file_type = "." + sample[self.filetype_key]
        if img_bytes:
            # 进行图片增强
            img_data = bytes_transform.bytes_to_numpy(img_bytes)
            img_data = self.enhance_sharpness(img_data, file_name)
            sample[self.data_key] = bytes_transform.numpy_to_bytes(img_data, file_type)
        logger.info("fileName: %s, method: ImgSharpness costs %.6f s",
                    file_name, time.time() - start)
        return sample
