# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 图片对比度自适应增强
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


class ImgContrast(Mapper):
    """图片对比度自适应增强"""

    def __init__(self, *args, **kwargs):
        super(ImgContrast, self).__init__(*args, **kwargs)
        # 自适应增强参数
        self.clip_limit = 2  # 指定对比度限制阈值, 较大的值会产生更大的对比度增强效(不作为参数传入)。
        self.tile_grid = 16  # 指定图像划分的网格大小,较小的网格大小会导致更局部的均衡化效果(不作为参数传入)。
        self.standard_mean = 100  # 图片增强后的平均对比度(不作为参数传入)。
        self.eps = 0.5  # 小值，计算图像对比度增强因子的时候，防止全黑图片导致的除零错(不作为参数传入)。

    @staticmethod
    def _get_contrast(image: np.ndarray):
        """计算图像所有通道的平均标准差"""
        _, stddev = cv2.meanStdDev(image)
        contrast_std = np.mean(stddev)
        return contrast_std

    def enhance_contrast(self, image_data: np.ndarray, file_name):
        """对比度自适应增强方法"""

        contrast_std = self._get_contrast(image_data)
        contrast_factor = self.standard_mean / (contrast_std + self.eps)

        # 图片对比度较高，不需要增强对比度
        if contrast_factor <= 1:
            logger.info("fileName: %s, method: ImgContrast not need enhancement", file_name)
            return image_data
        # 将彩色图像转换为Lab颜色空间
        cv2.cvtColor(image_data, cv2.COLOR_BGR2Lab, dst=image_data)

        # 使用局部自适应直方图均衡化进行对比度调整。
        clahe = cv2.createCLAHE(clipLimit=self.clip_limit, tileGridSize=(self.tile_grid, self.tile_grid))
        image_data[:, :, 0] = clahe.apply(image_data[:, :, 0])

        # 将增强后的Lab图像转换回BGR颜色空间
        cv2.cvtColor(image_data, cv2.COLOR_Lab2BGR, dst=image_data)
        return image_data

    def execute(self, sample: Dict[str, Any]):
        start = time.time()
        img_bytes = sample[self.data_key]
        file_name = sample[self.filename_key]
        file_type = "." + sample[self.filetype_key]
        if img_bytes:
            # 进行图片增强
            img_data = bytes_transform.bytes_to_numpy(img_bytes)
            img_data = self.enhance_contrast(img_data, file_name)
            sample[self.data_key] = bytes_transform.numpy_to_bytes(img_data, file_type)
        logger.info("fileName: %s, method: ImgContrast costs %.6f s",
                    file_name, time.time() - start)
        return sample
