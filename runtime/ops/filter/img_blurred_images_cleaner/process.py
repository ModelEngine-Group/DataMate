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
from datamate.core.base_op import Filter


class ImgBlurredImagesCleaner(Filter):
    """过滤模糊度低于阈值的图片插件"""

    def __init__(self, *args, **kwargs):
        super(ImgBlurredImagesCleaner, self).__init__(*args, **kwargs)
        # 设置模糊度阈值
        self._blurred_threshold = kwargs.get("blurredThreshold", 1000)

    def execute(self, sample: Dict[str, Any]):
        start = time.time()
        self.read_file_first(sample)
        img_bytes = sample[self.data_key]
        file_name = sample[self.filename_key]
        file_type = "." + sample[self.filetype_key]
        if img_bytes:
            data = bytes_transform.bytes_to_numpy(img_bytes)
            blurred_images = self._blurred_images_filter(data, file_name)
            sample[self.data_key] = bytes_transform.numpy_to_bytes(blurred_images, file_type)
        logger.info(f"fileName: {file_name}, method: ImagesBlurredCleaner costs {(time.time() - start):6f} s")
        return sample

    def _blurred_images_filter(self, image, file_name):
        # 为方便与其他图片比较可以将图片resize到同一个大小
        img_resize = cv2.resize(image, (112, 112))
        # 将图片压缩为单通道的灰度图
        gray = cv2.cvtColor(img_resize, cv2.COLOR_BGR2GRAY)
        score = cv2.Laplacian(gray, cv2.CV_64F).var()
        if score <= self._blurred_threshold:
            logger.info(f"The image blur is {self._blurred_threshold}, "
                        f"which exceeds the threshold of {score}. {file_name} is filtered out.")
            return np.array([])
        return image
