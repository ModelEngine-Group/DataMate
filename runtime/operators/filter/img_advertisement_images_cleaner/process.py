#!/usr/bin/env python
# -*- coding:utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description:
Create: 2024/1/22 20:49
"""
import logging as logger
import time
from typing import Dict, Any

import cv2
import numpy as np


from data_platform.common.utils import bytes_transform
from data_platform.core.base_op import Filter

from .wechat_qrcode_model import WechatQRCodeModel


class ImgAdvertisementImagesCleaner(Filter):
    """去除广告图片的插件，当前仅支持去除二维码"""

    def __init__(self, *args, **kwargs):
        super(ImgAdvertisementImagesCleaner, self).__init__(*args, **kwargs)
        self.img_resize = 1000  # 大图片的最长边压缩为1000
        self.use_model = True
        self.model = self.get_model(*args, **kwargs)

    @staticmethod
    def _detect_qr_code_using_anchor_point(img):
        # 有些二维码和边缘紧贴，无法识别出整个矩形，所以我们先对图片大小进行扩展
        expand_length = 10
        edge = expand_length // 2
        h, w = img.shape[:2]
        image_extend = np.zeros((img.shape[0] + expand_length, img.shape[1] + expand_length, 3), np.uint8)
        image_extend[:] = 255
        image_extend[edge:edge + h, edge:edge + w] = img

        # 转灰度、二值化、找轮廓
        gray = cv2.cvtColor(image_extend, cv2.COLOR_BGR2GRAY)
        # 中值滤波
        blur_image = cv2.medianBlur(gray, 5)
        _, thresh = cv2.threshold(blur_image, 127, 255, cv2.THRESH_BINARY)
        contours, hir = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # 三个“回”字特征轮廓存储
        parent_contours_list = []
        hir_list = hir[0]
        for i, item in enumerate(hir_list):
            # 判断A轮廓是否有B轮廓
            if item[2] == -1:
                continue
            else:
                hir_b_index = item[2]
            # 判断B轮廓是否有C轮廓
            if hir_list[hir_b_index][2] == -1:
                continue
            hir_c_index = hir_list[hir_b_index][2]
            # 计算A轮廓的周长和C轮廓周长的比值
            hir_c_arc_length = cv2.arcLength(contours[hir_c_index], True)
            if hir_c_arc_length:
                error = cv2.arcLength(contours[i], True) / hir_c_arc_length
                # 二维码每一个“回”的黑白框框的比例大概为1:1:3:1:1
                # 理论上，A轮廓周长为28，C轮廓周长为12，A/C = error = 2.3333
                if 1.5 <= error <= 3:
                    parent_contours_list.append(contours[i])

        # 若找到3个以上“回”字，该图片含有二维码
        return len(parent_contours_list) >= 3

    @staticmethod
    def _detect_qr_code_using_wechat_model(img, file_name, model):
        res = ""
        try:
            res, points = model.detectAndDecode(img)
        except UnicodeDecodeError as ex:
            res = ex.object.decode('ISO-8859-1').split(" ")[0]
        except Exception as err:
            logger.error("fileName: %s, method: ImgAdvertisementImagesCleaner. An error occurred when using "
                         "the WeChat model to detect the QR code. The error is: %s", file_name, err, exc_info=True)
        if res:
            return True
        return False

    def init_model(self, *args, **kwargs):
        return WechatQRCodeModel(*args, **kwargs).wechat_qr_model

    def resize_img(self, image):
        """图片等比压缩"""
        height, width = image.shape[:2]  # 获取原图像的水平方向尺寸和垂直方向尺寸。
        temp = max(height, width)
        # 若图片最长边大于限值，对图片进行压缩，否则返回原图
        if temp >= self.img_resize:
            mul_temp = temp / self.img_resize
            if height > width:
                res = cv2.resize(image, (int(width / mul_temp), self.img_resize), interpolation=cv2.INTER_AREA)
            elif height < width:
                res = cv2.resize(image, (self.img_resize, int(height / mul_temp)), interpolation=cv2.INTER_AREA)
            else:
                res = cv2.resize(image, (self.img_resize, self.img_resize), interpolation=cv2.INTER_AREA)
            return res
        return image

    def execute(self, sample: Dict[str, Any]):
        start = time.time()
        file_name = sample[self.filename_key]
        file_type = "." + sample[self.filetype_key]
        img_bytes = sample[self.data_key]
        if img_bytes:
            data = bytes_transform.bytes_to_numpy(img_bytes)
            image = self._detect_advertisement_img(data, file_name, self.model)
            sample[self.data_key] = bytes_transform.numpy_to_bytes(image, file_type)
            logger.info("fileName: %s, method: ImgAdvertisementImagesCleaner costs %.6f s", file_name,
                        time.time() - start)
        return sample

    def _detect_advertisement_img(self, img, file_name, model):
        """检测含有二维码的图片"""
        img_resize = self.resize_img(img)
        if self._detect_qr_code_using_wechat_model(img_resize, file_name, model) \
                or self._detect_qr_code_using_anchor_point(img_resize):
            logger.info("fileName: %s, method: ImgAdvertisementImagesCleaner. "
                        "The image contains advertisement. The image is filtered out.", file_name)
            return np.array([])
        return img
