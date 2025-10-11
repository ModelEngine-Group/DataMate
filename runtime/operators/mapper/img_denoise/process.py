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
from data_platform.core.base_op import Mapper


class ImgDenoise(Mapper):
    def __init__(self, *args, **kwargs):
        super(ImgDenoise, self).__init__(*args, **kwargs)
        self._denoise_threshold = kwargs.get("denoise_threshold", 8)

    @staticmethod
    def _denoise_image(data: object):
        """降噪处理"""
        return cv2.medianBlur(data, 3)

    def execute(self, sample: Dict[str, Any]):
        start = time.time()

        img_bytes = sample[self.data_key]

        file_name = sample[self.filename_key]
        file_type = "." + sample[self.filetype_key]
        if img_bytes:
            data = bytes_transform.bytes_to_numpy(img_bytes)
            denoise_images = self._denoise_images_filter(data, file_name)
            sample[self.data_key] = bytes_transform.numpy_to_bytes(denoise_images, file_type)
        logger.info("fileName: %s, method: ImgDenoise costs %.6f s", file_name, time.time() - start)
        return sample

    def _denoise_images_filter(self, ori_img, file_name):
        # 获取原始图片的去噪图片
        clean_data = self._denoise_image(ori_img)
        # 为方便与其他图片比较可以将图片resize到同一个大小
        ori = cv2.resize(ori_img, (112, 112))
        dst = cv2.resize(clean_data, (112, 112))
        # 计算未降噪图片的灰度值的集合
        signal = np.sum(ori ** 2)
        # 计算未降噪图片的灰度值与去噪图片灰度值的差值的集合
        noise = np.sum((ori - dst) ** 2)
        # 根据未去噪图片和差值计算snr (图片信噪比)
        snr = 10 * np.log10(signal / noise)
        # 对于小于阈值的图片，进行降噪处理
        if snr < self._denoise_threshold:
            logger.info("The image denoise is %s, which exceeds the threshold of %s. %s is filtered out.", snr,
                        self._denoise_threshold, file_name)
            return clean_data
        return ori_img
