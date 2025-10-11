# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description:
Create: 2024/1/30 9:26
"""
import logging as logger
import math
import time
from typing import Dict, Any

import cv2
import numpy as np

from data_platform.common.utils import bytes_transform
from data_platform.core.base_op import Mapper

from .base_model import BaseModel


class ImgDirectionCorrect(Mapper):
    def __init__(self, *args, **kwargs):
        super(ImgDirectionCorrect, self).__init__(*args, **kwargs)
        self.img_resize = 1000
        self.limit_size = 30000
        self.use_model = True
        self.vertical_model, self.standard_model = self.get_model(*args, **kwargs)

    @staticmethod
    def _detect_angle(img):
        """检测图片倾斜角度"""
        # 转为灰度单通道 [[255 255],[255 255]]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 黑白颠倒
        gray = cv2.bitwise_not(gray)
        # 二值化
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        # 把大于0的点的行列找出来
        ys, xs = np.where(thresh > 0)
        # 组成坐标[[306  37][306  38][307  38]],里面都是非零的像素
        coords = np.column_stack([xs, ys])
        # 获取最小矩形的信息 返回值(中心点，长宽，角度)
        rect = cv2.minAreaRect(coords)
        # 这里minAreaRect返回值为【0,90】，离y轴最近的夹角，后续有优化空间
        # 夹角小于45度时，填充的空白较少，有助于提升识别率
        angle = rect[-1]  # 最后一个参数是角度
        # 小于45度时，逆时针旋转45度
        if angle <= 45.0:
            return angle
        # 大于45度时，顺时针旋转（90-angle）
        return angle - 90

    @staticmethod
    def _detect_direction(image, file_name, model):
        """
        Args:
            image: 待预测的图片
            file_name: 文件名
            model: 使用的模型， vertical_model 和 standard_model
        Returns: 旋转后的图片
        """
        # cls_res为模型预测结果，格式应当类似于: [('90', 0.9815167)]
        _, cls_res, _ = model.infer([image])
        rotate_angle = int(cls_res[0][0])
        pro = float(cls_res[0][1])
        logger.info("fileName: %s, model %s detect result is %s with confidence %s", file_name, model.model_name,
                    rotate_angle, pro)
        if rotate_angle == 90 and pro > 0.89:
            return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        if rotate_angle == 180 and pro > 0.89:
            return cv2.rotate(image, 1)
        return image

    @staticmethod
    def _rotate_bound(image, angle):
        """根据倾斜角度旋转图片
        Args:
            image: 待处理图片
            angle: _detect_angle方法检测到的倾斜角
        """
        if angle == 0.0:
            return image
        # 获取宽高
        h, w = image.shape[:2]
        sinval = math.fabs(math.sin(angle))
        cosval = math.fabs(math.cos(angle))
        dx = max(int((w * cosval + h * sinval - w) / 2), 0)
        dy = max(int((w * sinval + h * cosval - h) / 2), 0)
        dst_img = cv2.copyMakeBorder(image, dy, dy, dx, dx, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        h, w = dst_img.shape[:2]
        rotated_matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        dst_img = cv2.warpAffine(dst_img, rotated_matrix, (w, h), borderValue=(255, 255, 255))
        return dst_img

    def init_model(self, *args, **kwargs):
        return BaseModel(model_type='vertical'), BaseModel(model_type='standard')

    def execute(self, sample: Dict[str, Any]):
        start = time.time()
        file_name = sample[self.filename_key]
        file_type = "." + sample[self.filetype_key]
        img_bytes = sample[self.data_key]
        if img_bytes:
            data = bytes_transform.bytes_to_numpy(img_bytes)
            correct_data = self._img_direction_correct(data, file_name, self.vertical_model, self.standard_model)
            sample[self.data_key] = bytes_transform.numpy_to_bytes(correct_data, file_type)
            logger.info("fileName: %s, method: ImgDirectionCorrect costs %.6f s", file_name,
                        time.time() - start)
        return sample

    def _img_direction_correct(self, img, file_name, vertical_model, standard_model):
        height, width = img.shape[:2]
        if max(height, width) > self.limit_size:
            logger.info(
                "fileName: %s, method: ImgDirectionCorrect cannot process pixels number larger than 30000",
                file_name)
            return img
        detect_angle_img = self._resize(img)
        # 检测旋转角
        angle = self._detect_angle(detect_angle_img)
        # 将图片处理为 0, 90, 180, 270旋转角度的图片
        rotated_img = self._rotate_bound(img, angle)
        # 水平垂直方向识别：二分类模型，检测图片方向角为 0, 90, 将其处理为 0和180二分类图片
        rotated_img = self._detect_direction(rotated_img, file_name, vertical_model)
        # 0-180方向识别：二分类模型，检测图片方向角为 0, 180, 将其处理为 0和180二分类图片
        rotated_img = self._detect_direction(rotated_img, file_name, standard_model)
        return rotated_img

    def _resize(self, image):
        height, width = image.shape[:2]  # 获取原图像的水平方向尺寸和垂直方向尺寸。
        temp = max(height, width)
        # 若图片最长边大于限值，对图片进行压缩，否则返回原图
        if temp >= self.img_resize:
            mul_temp = temp / self.img_resize
            if height > width:
                return cv2.resize(image, (int(width / mul_temp), self.img_resize), interpolation=cv2.INTER_AREA)
            elif height < width:
                return cv2.resize(image, (self.img_resize, int(height / mul_temp)), interpolation=cv2.INTER_AREA)
            else:
                return cv2.resize(image, (self.img_resize, self.img_resize), interpolation=cv2.INTER_AREA)
        return image
