# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 图片饱和度自适应增强
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


class ImgSaturation(Mapper):
    """图片饱和度自适应增强"""

    def __init__(self, *args, **kwargs):
        super(ImgSaturation, self).__init__(*args, **kwargs)
        # 自适应增强参数
        self.factor_threshold = 1.1  # 图片增强因子下限(不作为参数传入)。
        self.standard_mean = 130  # 图片增强后的平均饱和度(不作为参数传入)。
        self.eps = 1  # 极小值，计算图像饱和度增强因子的时候，防止全黑图片导致的除零错(不作为参数传入)。
        self.zeros_ratio_threshold = 0.1  # saturation通道 零值占比率，防止对近似灰度图的图像进行处理。
        self.red_channel_threshold = 140  # 图片红色通道阈值，用于抑制饱和度增强因子

    def enhance_saturation(self, image_data: np.ndarray, file_name):
        """饱和度自适应增强方法"""
        # 打开图像并转换为HSV颜色空间
        image_hsv = cv2.cvtColor(image_data, cv2.COLOR_BGR2HSV)
        s_channel = image_hsv[:, :, 1].copy()
        del image_hsv

        # 提取饱和度通道
        # 正常的RGB图片，零值占比率比应当小于0.1, 如果高于0.1，可以认为这张图片近似于灰度图
        zero_s_ratio = np.count_nonzero(s_channel == 0) / s_channel.size
        if zero_s_ratio <= self.zeros_ratio_threshold:
            saturation_channel = s_channel
        # 灰度图片转成的RGB图片，转为HSV后，S通道值全为0
        else:
            return image_data

        # 计算饱和度的统计信息
        saturation_mean = np.mean(saturation_channel)
        saturation_factor = self.standard_mean / (saturation_mean + self.eps)

        # 图片饱和度较高，不需要增强饱和度
        if saturation_factor <= 1:
            logger.info("fileName: %s, method: ImgSaturation not need enhancement", file_name)
            return image_data

        # 计算图片红色通道均值， 如果过大，需要限制saturation factor大小，否则图片会泛红, 产生色彩畸变。
        red_channel_mean = np.mean(image_data[:, :, 2])
        if red_channel_mean >= self.red_channel_threshold:
            saturation_factor = min(saturation_factor, 1.5)
        else:
            saturation_factor = max(saturation_factor, self.factor_threshold)

        degrade_image = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
        degrade_image = cv2.cvtColor(degrade_image, cv2.COLOR_GRAY2BGR)
        cv2.addWeighted(image_data, saturation_factor, degrade_image, 1 - saturation_factor, 0, dst=image_data)
        return image_data

    def execute(self, sample: Dict[str, Any]):
        start = time.time()
        img_bytes = sample[self.data_key]
        file_name = sample[self.filename_key]
        file_type = "." + sample[self.filetype_key]
        if img_bytes:
            # 进行图片增强
            img_data = bytes_transform.bytes_to_numpy(img_bytes)
            img_data = self.enhance_saturation(img_data, file_name)
            sample[self.data_key] = bytes_transform.numpy_to_bytes(img_data, file_type)
        logger.info("fileName: %s, method: ImgSaturation costs %.6f s",
                    file_name, time.time() - start)
        return sample
