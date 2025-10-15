#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 文档局部内容去重
Create: 2025/01/07
"""

import json
import logging as logger
import re
import time
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from datasketch import MinHash
from sqlalchemy import text

from data_platform.sql_manager.sql_manager import SQLManager
from data_platform.common.utils import get_now_time
from data_platform.core.base_op import Filter


class DuplicateFilesFilter(Filter):
    """相似文档去除插件

    基于MinHash计算当前文档与数据集中其它文档相似性，相似性高于设定阈值则返回空。
    """

    def __init__(self, *args, **kwargs):
        # 标点符号
        super().__init__(*args, **kwargs)
        self.punctuation_pattern = "。.？?！!，,；;：:（）()【】{}[]“”""‘’''/\n"
        # 默认相似度阈值为0.5
        self.duplicate_th = kwargs.get("fileDuplicateThreshold", 0.5)
        # task_uuid为标识该数据集的唯一标志
        self.task_uuid = kwargs.get("uuid", "uuid")
        # 数据库连接
        self.conn = None
        # 数据库事务
        self.trans = None
        # 每页数据量
        self.page_size = 500
        # 获取数据库sql
        self.sql_dict = self.load_sql_dict()

    @staticmethod
    def load_sql_dict():
        """获取sql语句"""
        sql_config_path = str(Path(__file__).parent / 'sql' / 'sql_config.json')
        with open(sql_config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_minhash(self, input_text: str) -> MinHash:
        """获取输入文档的minhash

        Args:
            input_text: 输入文档内容

        Returns:
            text_minhash: 输入文档对应的minhash值
        """
        text_minhash = MinHash()
        for word in re.split(f"[{re.escape(self.punctuation_pattern)}]", input_text.strip()):
            text_minhash.update(word.strip().encode('utf8'))
        return text_minhash

    def deduplicate_files(self, sample: Dict[str, Any], file_name: str) -> str:
        """去除相似文件

        Args:
            content: 待处理的Content对象
            file_name: 文件名称

        Returns:
            input_text: 去重后的文件内容，大于相似度值返回空，否则返回原始文本内容。
        """
        input_text = sample[self.text_key]
        if not input_text:
            return input_text
        text_minhash = self.get_minhash(input_text)
        return self.execute_sql(text_minhash, file_name, input_text)

    def execute_sql(self, text_minhash: MinHash, file_name: str,
                    input_text: str) -> str:
        """从数据库中获取文件特征、比较相似度，插入新的文件特征"""
        timestamp = get_now_time('Asia/Shanghai', '%Y-%m-%d %H:%M:%S', file_name,
                                 "DuplicateFilesFilter")
        minhash_values = text_minhash.hashvalues
        # 将 NumPy 数组转换为字符串
        minhash_values_string = np.array2string(minhash_values)
        query_task_uuid_sql = self.sql_dict.get("query_task_uuid_sql")
        insert_sql = self.sql_dict.get("insert_sql")
        create_tables_sql = self.sql_dict.get("create_tables_sql")
        db_manager = SQLManager()
        try:
            self.conn = db_manager.create_connect()
        except Exception as e:
            logger.error("fileName: %s, database connection failed: %s", file_name, str(e))
            raise RuntimeError(82000, str(e)) from None
        with self.conn as connection:
            connection.execute(text(create_tables_sql))
            result = connection.execute(query_task_uuid_sql, {"task_uuid": self.task_uuid}).fetchall()
            total_count = len(result)
            if self.has_similar_text(connection, file_name, text_minhash, total_count):
                return ""
            insert_data = {
                "task_uuid": self.task_uuid,
               "file_feature": minhash_values_string,
               "file_name": file_name.encode("utf-8").hex(),
               "timestamp": timestamp
            }
            connection.execute(text(insert_sql), insert_data)
        return input_text

    def has_similar_text(self, connection, file_name, text_minhash, total_count) -> bool:
        query_sql = self.sql_dict.get("query_sql")
        for i in range(0, total_count, self.page_size):
            rows = connection.execute(
                text(query_sql), {"task_uuid": self.task_uuid, "ge": self.page_size, "le": i}).fetchall()
            # 对应任务uuid，最后一页没有数据，跳出循环
            if not rows:
                break
            # 对两个文本进行相似度比较
            if self.determine_similar_text(rows, text_minhash, file_name):
                return True
        return False

    def determine_similar_text(self, file_features: List, text_minhash: MinHash, file_name: str) -> bool:
        for signature in file_features:
            # 历史文件特征和历史文件名称
            file_feature, file_name_history = signature[2], signature[3]
            if not file_feature:
                continue
            minhash_obj = MinHash(num_perm=128)
            minhash_obj.hashvalues = np.fromstring(file_feature.strip('[]'), dtype=np.uint64, sep=' ')
            similarity = text_minhash.jaccard(minhash_obj)

            # 移除转义字符 '\' 并将十六进制字符串转换为字节序列
            bytes_data = bytes.fromhex(file_name_history)
            # 解码字节序列为 UTF-8 编码的字符串
            file_name_decoded = bytes_data.decode('utf-8')

            if similarity >= self.duplicate_th:
                logger.info("dataset: %s, fileName: %s is similar to %s, and the similarity is %.4f",
                            self.task_uuid, file_name, file_name_decoded, similarity)
                return True
        return False

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        file_name = sample[self.filename_key]
        sample[self.text_key] = self.deduplicate_files(sample, file_name)
        logger.info("fileName: %s, method: DuplicateFilesFilter costs %.6f s", file_name, time.time() - start)
        return sample
