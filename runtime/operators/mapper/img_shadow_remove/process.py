# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 图片去阴影插件
Create: 2025/01/16
"""
import time

import logging as logger
from typing import Dict, Any

import cv2
import numpy as np

from data_platform.common.utils import bytes_transform
from data_platform.core.base_op import Mapper


class ImgShadowRemove(Mapper):
    """图片阴影去除"""

    def __init__(self, *args, **kwargs):
        super(ImgShadowRemove, self).__init__(*args, **kwargs)
        self.iter_nums = 9  # 闭运算循环次数(不作为参数传入)。
        self.k_size = 3  # kernel size大小。
        self.clip_limit = 2  # 对比度限制阈值, 数值越大，效果越强。
        self.tile_grid = 8  # 图像划分的网格大小, 数值越小，局部效果越明显。

    def shadow_removed(self, image_data: np.ndarray):
        '''
        阴影去除。

        Args:
            image_data: nd.array 格式图片
        Returns:
            阴影去除后的图片
        '''
        # 设置kernel大小，进行闭运算
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (self.k_size, self.k_size))
        closing = cv2.morphologyEx(image_data, cv2.MORPH_CLOSE, kernel, iterations=self.iter_nums)

        # 进行~（closing - original）操作
        cv2.bitwise_not(closing - image_data, dst=closing)
        cv2.cvtColor(closing, cv2.COLOR_BGR2Lab, dst=closing)

        # 获取处理后图像的亮度通道
        img_l = cv2.split(closing)[0]
        del closing

        # 对img_l进行调节后，替换原图的亮度通道
        cv2.cvtColor(image_data, cv2.COLOR_BGR2Lab, dst=image_data)
        # 创建 CLAHE 对象
        clahe = cv2.createCLAHE(clipLimit=self.clip_limit, tileGridSize=(self.tile_grid, self.tile_grid))
        # 进行 CLAHE 处理
        image_data[:, :, 0] = clahe.apply(img_l)
        del img_l

        cv2.cvtColor(image_data, cv2.COLOR_Lab2BGR, dst=image_data)
        return image_data

    def execute(self, sample: Dict[str, Any]):
        start = time.time()
        img_bytes = sample[self.data_key]
        file_name = sample[self.filename_key]
        file_type = "." + sample[self.filetype_key]
        if img_bytes:
            # 进行阴影去除
            img_data = bytes_transform.bytes_to_numpy(img_bytes)
            img_data = self.shadow_removed(img_data)
            sample[self.data_key] = bytes_transform.numpy_to_bytes(img_data, file_type)
        logger.info("fileName: %s, method: ImageShadowRemove costs %.6f s",
                    file_name, time.time() - start)
        return sample
