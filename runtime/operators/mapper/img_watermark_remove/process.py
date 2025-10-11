# # -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
#
# Description:
# Create: 2025/01/06
# """
import logging as logger
import time
from typing import Dict, Any

import cv2
import numpy as np

from data_platform.common.utils import bytes_to_numpy
from data_platform.common.utils import numpy_to_bytes
from data_platform.core.base_op import Mapper
from .watermark_ocr_model import WatermarkOcrModel

DEFAULT_MAX_CHARACTERS = 10
DEFAULT_BINARY_THRESHOLD_LOW = 200


class ImgWatermarkRemove(Mapper):
    use_model = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remove_str = kwargs.get("watermarkStr", "知乎,抖音")
        self.ocr_model = self.get_model(*args, **kwargs)

    @staticmethod
    def _has_kw(result_list, kw_list):
        """
        图片是否包含目标水印，返回匹配到的文字列表
        """
        result_str_list = []
        for line in result_list:
            for kw in kw_list:
                if kw in line[1][0]:
                    result_str_list.append(line[1][0])
                    break
        return result_str_list

    @staticmethod
    def _overlay_mask(background_img, prospect_img, img_over_x, img_over_y):
        back_r, back_c, _ = background_img.shape  # 背景图像行数、列数
        is_x_direction_failed = img_over_x > back_c or img_over_x < 0
        is_y_direction_failed = img_over_y > back_r or img_over_y < 0
        if is_x_direction_failed or is_y_direction_failed:
            # 前景图不在背景图范围内, 直接返回原图
            return background_img
        pro_r, pro_c, _ = prospect_img.shape  # 前景图像行数、列数
        if img_over_x + pro_c > back_c:  # 如果水平方向展示不全
            pro_c = back_c - img_over_x  # 截取前景图的列数
            prospect_img = prospect_img[:, 0:pro_c, :]  # 截取前景图
        if img_over_y + pro_r > back_r:  # 如果垂直方向展示不全
            pro_r = back_r - img_over_y  # 截取前景图的行数
            prospect_img = prospect_img[0:pro_r, :, :]  # 截取前景图

        prospect_img = cv2.cvtColor(prospect_img, cv2.COLOR_BGR2BGRA)  # 前景图转为4通道图像
        prospect_tmp = np.zeros((back_r, back_c, 4), np.uint8)  # 与背景图像等大的临时前景图层

        # 前景图像放到前景图层里
        prospect_tmp[img_over_y:img_over_y + pro_r, img_over_x: img_over_x + pro_c, :] = prospect_img

        _, binary = cv2.threshold(prospect_img, 254, 255, cv2.THRESH_BINARY)  # 前景图阈值处理
        prospect_mask = np.zeros((pro_r, pro_c, 1), np.uint8)  # 单通道前景图像掩模
        prospect_mask[:, :, 0] = binary[:, :, 3]  # 不透明像素的值作为掩模的值

        mask = np.zeros((back_r, back_c, 1), np.uint8)
        mask[img_over_y:img_over_y + prospect_mask.shape[0],
        img_over_x: img_over_x + prospect_mask.shape[1]] = prospect_mask

        mask_not = cv2.bitwise_not(mask)

        prospect_tmp = cv2.bitwise_and(prospect_tmp, prospect_tmp, mask=mask)
        background_img = cv2.bitwise_and(background_img, background_img, mask=mask_not)
        prospect_tmp = cv2.cvtColor(prospect_tmp, cv2.COLOR_BGRA2BGR)  # 前景图层转为三通道图像
        return prospect_tmp + background_img  # 前景图层与背景图像相加合并

    def execute(self, sample: Dict[str, Any]):
        start = time.time()
        file_name = sample[self.filename_key]
        file_type = "." + sample[self.filetype_key]
        img_bytes = sample[self.data_key]
        if img_bytes:
            data = bytes_to_numpy(img_bytes)
            correct_data = self._watermark_remove(data, file_name, self.ocr_model)
            sample[self.data_key] = numpy_to_bytes(correct_data, file_type)
        logger.info("fileName: %s, method: ImgWatermarkRemove costs %.6f s", file_name, time.time() - start)
        return sample

    def delete_watermark(self, result_list, kw_list, data):
        """
        将符合目标的水印，模糊化处理
        """
        # 获取所有符合目标的文本框位置
        text_axes_list = []
        for line in result_list:
            for kw in kw_list:
                if kw in line[1][0]:
                    min_width = int(min(line[0][0][0], line[0][3][0]))
                    max_width = int(max(line[0][1][0], line[0][2][0]))
                    min_hight = int(min(line[0][0][1], line[0][1][1]))
                    max_hight = int(max(line[0][2][1], line[0][3][1]))
                    text_axes_list.append([min_width, min_hight, max_width, max_hight])
                    break
        # 去除水印
        delt = DEFAULT_MAX_CHARACTERS  # 文本框范围扩大
        img = data
        for text_axes in text_axes_list:
            hight, width = img.shape[0:2]
            # 截取图片
            min_width = text_axes[0] - delt if text_axes[0] - delt >= 0 else 0
            min_hight = text_axes[1] - delt if text_axes[1] - delt >= 0 else 0
            max_width = text_axes[2] + delt if text_axes[2] + delt <= width else width
            max_hight = text_axes[3] + delt if text_axes[3] + delt <= hight else hight
            cropped = img[min_hight:max_hight, min_width:max_width]  # 裁剪坐标为[y0:y1, x0:x1]
            # 图片二值化处理，把[200,200,200]-[250,250,250]以外的颜色变成0
            start_rgb = DEFAULT_BINARY_THRESHOLD_LOW
            thresh = cv2.inRange(cropped, np.array([start_rgb, start_rgb, start_rgb]), np.array([250, 250, 250]))
            # 创建形状和尺寸的结构元素
            kernel = np.ones((3, 3), np.uint8)  # 设置卷积核3*3全是1；将当前的数组作为图像类型来进&#12175;各种操作，就要转换到uint8类型
            # 扩展待修复区域
            hi_mask = cv2.dilate(thresh, kernel, iterations=10)  # 膨胀操作，白色区域增大，iterations迭代次数
            specular = cv2.inpaint(cropped, hi_mask, 5, flags=cv2.INPAINT_TELEA)
            # imgSY：输入8位1通道或3通道图像。
            # hi_mask：修复掩码，8位1通道图像。非零像素表示需要修复的区域。
            # specular：输出与imgSY具有相同大小和类型的图像。
            # 5：算法考虑的每个点的圆形邻域的半径。
            # flags：NPAINT_NS基于Navier-Stokes的方法、Alexandru Telea的INPAINT_TELEA方法
            result = self._overlay_mask(img, specular, min_width, min_hight)
            img = result
        return img

    def init_model(self, *args, **kwargs):
        return WatermarkOcrModel(*args, **kwargs).ocr_model

    def _watermark_remove(self, data, file_name, model):
        """
        去除水印的方法
        """
        remove_str = self.remove_str
        # 勾选去水印的信息为空，则直接返回原图
        if remove_str == "":
            return data
        kw_list = remove_str.split(',')
        # 加载模型
        ocr_model = model
        try:
            result = ocr_model.ocr(data, cls=True)
        except RuntimeError as e:
            logger.error("fileName: %s, method: ocr predict error %s", file_name, e)
            return data
        if result and result[0]:
            logger.info("fileName: %s, method: ocrModel detect watermark info %s", file_name, str(result))
            return self.delete_watermark(result[0], kw_list, data)
        else:
            logger.info("fileName: %s, method: ImgWatermarkRemove not need remove target ocr", file_name)
            return data
