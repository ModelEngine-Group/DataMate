#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: Json文本抽取
Create: 2024/06/06 15:43
"""
import time
import logging as logger
from typing import Dict, Any

from data_platform.core.base_op import Mapper


class TextFormatter(Mapper):
    """把输入的json文件流抽取为txt"""

    def __init__(self, *args, **kwargs):
        super(TextFormatter, self).__init__(*args, **kwargs)

    @staticmethod
    def _extract_json(byte_io):
        """将默认使用utf-8编码的Json文件流解码，抽取为txt"""
        # 用utf-8-sig的格式进行抽取，可以避免uft-8 BOM编码格式的文件在抽取后产生隐藏字符作为前缀。
        return byte_io.decode("utf-8-sig").replace("\r\n", "\n")

    def byte_read(self, sample: Dict[str, Any]):
        filepath = sample[self.filepath_key]
        with open(filepath, "rb") as file:
            byte_data = file.read()
        sample[self.data_key] = byte_data

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        try:
            self.byte_read(sample)
            sample[self.text_key] = self._extract_json(sample[self.data_key])
            sample[self.data_key] = b""  # 将sample[self.data_key]置空
            logger.info("fileName: %s, method: TextFormatter costs %.6f s",
                        sample[self.filename_key], time.time() - start)
        except UnicodeDecodeError as err:
            logger.error("fileName: %s, method: TextFormatter causes decode error: %s",
                         sample[self.filename_key], err, exc_info=True)
            raise
        return sample
