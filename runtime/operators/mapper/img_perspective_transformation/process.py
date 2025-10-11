# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description:
Create: 2025/01/16
"""
import time

import logging as logger
from typing import Dict, Any

import cv2
import numpy as np

from data_platform.common.utils import bytes_transform
from data_platform.core.base_op import Mapper


class ImgPerspectiveTransformation(Mapper):
    """图片透视变换插件"""

    def __init__(self, *args, **kwargs):
        super(ImgPerspectiveTransformation, self).__init__(*args, **kwargs)
        self.transform_utils = PerspectiveTransformationUtils()

    def execute(self, sample: Dict[str, Any]):
        start = time.time()
        img_bytes = sample[self.data_key]
        file_name = sample[self.filename_key]
        file_type = "." + sample[self.filetype_key]
        if img_bytes:
            img_data = bytes_transform.bytes_to_numpy(img_bytes)
            transform_img = self._transform_img(img_data, file_name)
            sample[self.data_key] = bytes_transform.numpy_to_bytes(transform_img, file_type)
        logger.info("fileName: %s, method: ImgPerspectiveTransformation costs %.6f s", file_name,
                    time.time() - start)
        return sample

    def _transform_img(self, image, file_name):
        original_img = image
        ratio = 900 / image.shape[0]
        # 固定尺寸
        img_resize = self.transform_utils.resize_img(image)
        # 边缘检测
        binary_img = self.transform_utils.get_canny(img_resize)
        # 轮廓
        max_contour, max_area = self.transform_utils.find_max_contour(binary_img)
        if not max_contour.size:
            return original_img
        # 多边形拟合凸包的四个顶点
        boxes = self.transform_utils.get_box_point(max_contour)
        if len(boxes) == 4:
            boxes = self.transform_utils.get_adapt_point(boxes, ratio)
            boxes = self.transform_utils.order_points(boxes)
            warped = self.transform_utils.get_warp_image(image, boxes)
            logger.info("fileName: %s, method: ImgPerspectiveTransformation. "
                        "This picture is transformed by perspective.", file_name)
            return warped
        return original_img


class PerspectiveTransformationUtils:
    """图片透视变换工具类"""

    @staticmethod
    def resize_img(image, height=900):
        """固定尺寸"""
        h, w = image.shape[:2]
        pro = height / h
        size = (int(w * pro), int(height))
        img_resize = cv2.resize(image, size)
        return img_resize

    @staticmethod
    def get_canny(image):
        """边缘检测"""
        # 高斯滤波
        binary = cv2.GaussianBlur(image, (3, 3), 2, 2)
        # 边缘检测
        binary = cv2.Canny(binary, 60, 240, apertureSize=3)
        # 膨胀操作，尽量使边缘闭合
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.dilate(binary, kernel, iterations=1)
        return binary

    @staticmethod
    def find_max_contour(image):
        """求出面积最大的轮廓"""
        # 寻找边缘
        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        # 计算面积
        max_area = 0.0
        max_contour = np.array([])
        for contour in contours:
            current_area = cv2.contourArea(contour)
            if current_area > max_area:
                max_area = current_area
                max_contour = contour
        return max_contour, max_area

    @staticmethod
    def get_box_point(contour):
        """多边形拟合凸包的四个顶点"""
        # 多边形拟合凸包
        hull = cv2.convexHull(contour)
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(hull, epsilon, True)
        approx = approx.reshape((len(approx), 2))
        return approx

    @staticmethod
    def get_adapt_point(box, pro):
        """适配原四边形点集"""
        box_pro = box
        if pro != 1.0:
            box_pro = box / pro
        box_pro = np.trunc(box_pro)
        return box_pro

    @staticmethod
    def order_points(pts):
        """四边形顶点排序，[top-left, top-right, bottom-right, bottom-left]"""
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return np.intp(rect)

    @staticmethod
    def compute_point_distance(a, b):
        """计算长宽"""
        return int(np.sqrt(np.sum(np.square(a - b))))

    def get_warp_image(self, image, box):
        """透视变换"""
        w, h = self.compute_point_distance(box[0], box[1]), \
            self.compute_point_distance(box[1], box[2])
        dst_rect = np.array([[0, 0],
                             [w - 1, 0],
                             [w - 1, h - 1],
                             [0, h - 1]], dtype='float32')
        box = np.array(box, dtype='float32')
        matrix = cv2.getPerspectiveTransform(box, dst_rect)
        warped = cv2.warpPerspective(image, matrix, (w, h))
        return warped
