# -- encoding: utf-8 --

"""
Description:
Create: 2025/01/17
"""
import time

from typing import Dict, Any

import cv2
import numpy as np
from loguru import logger

from datamate.common.utils import bytes_transform
from datamate.core.base_op import Mapper


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
        self.read_file_first(sample)

        img_bytes = sample[self.data_key]

        file_name = sample[self.filename_key]
        file_type = "." + sample[self.filetype_key]
        if img_bytes:
            data = bytes_transform.bytes_to_numpy(img_bytes)
            denoise_images = self._denoise_images_filter(data, file_name)
            sample[self.data_key] = bytes_transform.numpy_to_bytes(denoise_images, file_type)
        logger.info(f"fileName: {file_name}, method: ImgDenoise costs {time.time() - start:6f} s")
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
            logger.info(f"The image denoise is {self._denoise_threshold}, "
                        f"which exceeds the threshold of {snr}. {file_name} is filtered out.")
            return clean_data
        return ori_img
