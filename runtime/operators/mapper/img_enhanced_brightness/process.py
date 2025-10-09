# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 图像亮度增强算子。
Create: 2025/01/13
"""

import time

import logging as logger
from typing import Dict, Any

import numpy as np
import cv2

from data_platform.common.utils import bytes_transform

from data_platform.core.base_op import Mapper


class ImgBrightness(Mapper):
    """图片亮度自适应增强"""

    def __init__(self, *args, **kwargs):
        super(ImgBrightness, self).__init__(*args, **kwargs)
        # 自适应增强参数
        self.factor_threshold = 1.1  # 图片增强因子下限(不作为参数传入)。
        self.standard_mean = 140  # 图片增强后的平均亮度(不作为参数传入)。
        self.gamma = 1.5  # gamma correction 中的gamma系数，大于1时，使得图像变亮。小于1时，使得图像变暗(不作为参数传入)。
        self.brightness_upper_bound = 0.35  # 非线性亮度增强阈值上界: 超过这个百分比，就进行线性亮度增强(不作为参数传入)。
        self.eps = 1  # 极小值，计算图像亮度增强因子的时候，防止全黑图片导致的除零错(不作为参数传入)。

    @staticmethod
    def _get_grey_mean(src: np.ndarray):
        gray_image = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
        return np.mean(gray_image)

    @staticmethod
    def _return_gamma_table(gamma):
        """返回gamma校正对应的查找表"""
        scale = np.power(255, 1 - gamma).astype(np.float64)
        return np.power(np.arange(256), gamma) * scale

    @staticmethod
    def _return_linear_table(factor):
        """返回线性变换对应的查找表"""
        linear_table = np.arange(256) * factor
        return np.clip(linear_table, 0, 255).astype(np.uint8)

    def enhance_brightness_linear(self, image_data: np.ndarray, file_name):
        average_brightness = self._get_grey_mean(image_data)
        brightness_factor = self.standard_mean / (average_brightness + self.eps)

        # 图像过亮，不需要增强亮度
        if brightness_factor <= 1:
            logger.info("fileName: %s, method: ImgBrightness not need enhancement", file_name)
            return image_data

        brightness_factor = max(brightness_factor, self.factor_threshold)
        linear_table = ImgBrightness._return_linear_table(brightness_factor)
        cv2.LUT(image_data, linear_table, dst=image_data)
        return image_data

    def enhance_brightness(self, image_data: np.ndarray, file_name):
        '''
        亮度自适应增强方法。

        Args:
            image_data: nd.array 格式图片
            gamma: gamma变换因子参数。经验值常用1.5, 已写成了成员变量。
        Returns:
            亮度自适应增强后的图片
        '''
        # 计算图片平均亮度
        average_brightness = self._get_grey_mean(image_data)

        # 进行 gamma 校正
        if average_brightness / 255 <= self.brightness_upper_bound:
            # 预计算查找表
            gamma_table = ImgBrightness._return_gamma_table(1 / self.gamma).astype(np.uint8)
            cv2.LUT(image_data, gamma_table, dst=image_data)

        # 如果亮度超过非线性亮度调整的上界，就进行非线性亮度调整
        else:
            image_data = self.enhance_brightness_linear(image_data, file_name)

        return image_data

    def execute(self, sample: Dict[str, Any]):
        start = time.time()
        img_bytes = sample[self.data_key]
        file_name = sample[self.filename_key]
        file_type = "." + sample[self.filetype_key]
        if img_bytes:
            # 进行图片增强
            img_data = bytes_transform.bytes_to_numpy(img_bytes)
            img_data = self.enhance_brightness(img_data, file_name)
            sample[self.data_key] = bytes_transform.numpy_to_bytes(img_data, file_type)
        logger.info("fileName: %s, method: ImgBrightness costs %.6f s",
                    file_name, time.time() - start)
        return sample
