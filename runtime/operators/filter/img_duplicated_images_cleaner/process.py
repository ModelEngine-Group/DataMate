# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description:
于MD5值计算当前图片与数据集中其它图片是否相同。相同该图片过滤，保留原数据集图片。
将文件特征数据即MD5值，存到数据库。根据任务uuid获取历史文件特征，遍历特征并进行去重比较
Create: 2025/1/7
"""

import json
import logging as logger
import time
from pathlib import Path
from typing import Dict, Any

import cv2
from Crypto.Hash import MD5
from sqlalchemy import text

from data_platform.sql_manager.sql_manager import SQLManager
from data_platform.common.utils import get_now_time
from data_platform.common.utils import bytes_to_numpy, numpy_to_bytes
from data_platform.core.base_op import Filter


class ImgDuplicatedImagesCleaner(Filter):
    """去除重复图片插件
    基于MD5值计算当前图片与数据集中其它图片是否相同。相同该图片过滤，保留原数据集图片。
    """

    def __init__(self, *args, **kwargs):
        # task_uuid为标识该数据集的唯一标志
        super().__init__(*args, **kwargs)
        self.task_uuid = kwargs.get("uuid", "uuid")
        self.img_resize = 200  # 图片压缩尺寸
        # 获取数据库sql
        self.sql_dict = self.load_sql_dict()
        # 获取数据库连接池
        self.conn = None  # 数据库连接
        self.trans = None  # 数据库事务

    @staticmethod
    def load_sql_dict():
        """获取sql语句"""
        sql_config_path = str(Path(__file__).parent / 'sql' / 'sql_config.json')
        with open(sql_config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def compute_md5(self, img_bytes: bytes) -> str:
        """将图片统一转化为png无损格式，计算每张图像的md5值"""
        if not img_bytes:
            return ""
        img = bytes_to_numpy(img_bytes)
        height, width = img.shape[:2]  # 获取原图像的水平方向尺寸和垂直方向尺寸。
        res = cv2.resize(img, (int(width / height * self.img_resize), self.img_resize), interpolation=cv2.INTER_AREA)
        img_bytes = numpy_to_bytes(res, ".png")
        hash_md5 = MD5.new()
        hash_md5.update(img_bytes)
        return hash_md5.hexdigest()

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """重复图片去重算子执行入口"""
        start = time.time()
        file_name = sample[self.filename_key]
        img_data = self._duplicate_images_filter(file_name, sample[self.data_key])
        sample[self.data_key] = img_data
        logger.info(
            "fileName: %s, method: DuplicateImagesCleaner costs %.6f s", file_name, time.time() - start)
        return sample

    def execute_sql(self, md5: str, file_name: str,
                    img_bytes: bytes) -> bytes:
        """从数据库中获取文件特征、比较MD5，插入新的文件特征"""
        timestamp = get_now_time('Asia/Shanghai', '%Y-%m-%d %H:%M:%S', file_name,
                                 "DuplicateImagesCleaner")
        query_sql = str(self.sql_dict.get("query_sql"))
        insert_sql = str(self.sql_dict.get("insert_sql"))
        create_tables_sql = str(self.sql_dict.get("create_tables_sql"))
        query_sql_params = {"task_uuid": self.task_uuid, "file_feature": md5}
        insert_sql_params = {"task_uuid": self.task_uuid, "file_feature": md5, "file_name": file_name.encode("utf-8"),
                             "timestamp": timestamp}

        db_manager = SQLManager()
        try:
            self.conn = db_manager.create_connect()
        except Exception as e:
            logger.error("fileName: %s, database connection failed: %s", file_name, str(e))
            raise RuntimeError(82000, str(e)) from None

        with self.conn as connection:
            connection.execute(text(create_tables_sql))
            # 判断是否有重复文件
            result = connection.execute(text(query_sql, query_sql_params)).fetchall()
            # 查询记录为空，无重复图片, 插入新文件特征
            if not result:
                connection.execute(text(insert_sql, insert_sql_params))
                return img_bytes
            logger.info("fileName: %s, method: Duplicate ImagesCleaner. The image is duplicated and filtered ",
                        file_name)
        return b""

    def _duplicate_images_filter(self, file_name: str, img_bytes: bytes) -> bytes:
        """重复图片去重算子执行逻辑"""
        # 如果文件为空，则无需去重，返回原图
        if not img_bytes:
            return img_bytes
        md5 = self.compute_md5(img_bytes)
        return self.execute_sql(md5, file_name, img_bytes)
