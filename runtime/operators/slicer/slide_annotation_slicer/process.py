# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 医疗图片按坐标切片
Create: 2025/02/08 11:00
"""
import copy
import time
import os
from typing import List, Dict, Any

import xml.etree.ElementTree as ET
from loguru import logger

import numpy as np
import cv2
from openslide import OpenSlide

from data_platform.core.base_op import Slicer
from data_platform.common.utils import bytes_transform


class AnnotationSlicer(Slicer):

    def __init__(self, *args, **kwargs):
        super(AnnotationSlicer, self).__init__(*args, **kwargs)
        self.last_ops = True

    def execute(self, sample: Dict[str, Any]) -> List[Dict[str, Any]]:
        start = time.time()

        slide: OpenSlide = OpenSlide(sample[self.filepath_key])
        if not isinstance(slide, OpenSlide):
            logger.error("Not desired <Image.Image> object.")

        annotation_path: str = sample["extraFilePath"]
        annotations = self.parse_xml_annotations(annotation_path)

        patch_num = self.auto_coordinate_slicer(sample, slide, annotations)
        sample["slice_num"] = patch_num

        file_name = sample[self.filename_key]
        logger.info("fileName: %s, method: CoordinateSlider costs %.6f s", file_name, time.time() - start)

        return [sample]

    def parse_xml_annotations(self, xml_path: str) -> List:
        """ 解析 XML 文件，提取所有 Annotation 的坐标和 PartOfGroup """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        annotations = []

        # 找到所有 <Annotations> 标签
        annotations_tag = root.find('Annotations')
        if annotations_tag is None:
            raise ValueError("未找到 Annotations 标签")

        # 遍历所有 <Annotation> 标签
        for annotation in annotations_tag.findall('Annotation'):
            part_of_group = annotation.get('PartOfGroup')
            coordinates = []
            for coord in annotation.find('Coordinates').findall('Coordinate'):
                x = float(coord.get('X'))
                y = float(coord.get('Y'))
                coordinates.append((x, y))
            annotations.append({
                'part_of_group': part_of_group,
                'coordinates': np.array(coordinates, dtype=np.int32)
            })

        return annotations

    def auto_coordinate_slicer(
            self,
            original_sample: Dict,
            slide: OpenSlide,
            annotations: List
    ) -> int:
        """
        自动根据给定的标注文件切片原图像

        Return: 
            List[Content] 每个 content 都是一个 data 为 patch 的 content
        """
        wsi_width, wsi_height = slide.dimensions

        patch_no = 0
        # 遍历每个 Annotation
        for _, annotation in enumerate(annotations):
            part_of_group = annotation['part_of_group']
            coordinates = annotation['coordinates']

            # 转换坐标为整数（确保在图像范围内）
            coordinates = coordinates.clip(min=0, max=(wsi_width, wsi_height))

            # 创建掩码（mask）图像
            mask = np.zeros((wsi_height, wsi_width), dtype=np.uint8)
            cv2.fillPoly(mask, [coordinates], 255)  # 填充多边形区域为白色

            # 找到掩码中的非零区域（肿瘤区域）
            x, y, w, h = cv2.boundingRect(coordinates)  # 获取多边形的边界框

            # 读取 WSI 图像的切片区域
            region = slide.read_region((x, y), 0, (w, h))

            # 转换为 NumPy 数组
            region_np = np.array(region.convert("RGB"))

            patch_sample = copy.deepcopy(original_sample)
            patch_sample[self.data_key] = bytes_transform.numpy_to_bytes(region_np, '.png')
            patch_no += 1
            self.save_patch_sample(patch_sample, patch_no, save_format="image")

        logger.info(f">>> {patch_no} annotations found and sliced.")

        return patch_no
