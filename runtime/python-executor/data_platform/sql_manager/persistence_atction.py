# -*- coding: utf-8 -*-

import json
import time
import os
from pathlib import Path
from typing import Dict, Any

from loguru import logger
from sqlalchemy import text

from data_platform.sql_manager.sql_manager import SQLManager


class TaskInfoPersistence:
    def __init__(self):
        self.sql_dict = self.load_sql_dict()

    @staticmethod
    def load_sql_dict():
        """获取sql语句"""
        sql_config_path = str(Path(__file__).parent / 'sql' / 'sql_config.json')
        with open(sql_config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def persistence_task_info(self, sample: Dict[str, Any]):
        instance_id = str(sample.get("instance_id"))
        meta_file_name = str(sample.get("sourceFileName"))
        meta_file_type = str(sample.get("sourceFileType"))
        meta_file_id = int(sample.get("sourceFileId"))
        meta_file_size = str(sample.get("sourceFileSize"))
        file_id = int(sample.get("fileId"))
        file_size = str(sample.get("fileSize"))
        file_type = str(sample.get("fileType"))
        file_name = str(sample.get("fileName"))
        file_path = str(sample.get("filePath"))
        status = int(sample.get("execute_status"))
        failed_reason = sample.get("failed_reason")
        operator_id = str(failed_reason.get("op_name")) if failed_reason else ""
        error_code = str(failed_reason.get("error_code")) if failed_reason else ""
        incremental = str(sample.get("incremental") if sample.get("incremental") else '')
        child_id = sample.get("childId")
        slice_num = sample.get('slice_num', 0)
        insert_data = {
            "instance_id": instance_id,
            "meta_file_id": meta_file_id,
            "meta_file_type": meta_file_type,
            "meta_file_name": meta_file_name,
            "meta_file_size": meta_file_size,
            "file_id": file_id,
            "file_size": file_size,
            "file_type": file_type,
            "file_name": file_name,
            "file_path": file_path,
            "status": status,
            "operator_id": operator_id,
            "error_code": error_code,
            "incremental": incremental,
            "child_id": child_id,
            "slice_num": slice_num,
        }
        self.insert_clean_result(insert_data)

    def insert_clean_result(self, insert_data):
        retries = 0
        max_retries = 20
        retry_delay = 1
        while retries <= max_retries:
            try:
                self.execute_sql_insert(insert_data)
                return
            except Exception as e:
                if "database is locked" in str(e) or "locking protocol" in str(e):
                    retries += 1
                    time.sleep(retry_delay)
                else:
                    logger.error("database execute failed: {}", str(e))
                    raise RuntimeError(82000, str(e)) from None
        raise Exception("Max retries exceeded")

    def execute_sql_insert(self, insert_data):
        insert_sql = str(self.sql_dict.get("insert_sql"))
        create_tables_sql = str(self.sql_dict.get("create_tables_sql"))
        with SQLManager.create_connect() as conn:
            conn.execute(text(create_tables_sql))
            conn.execute(text(insert_sql), insert_data)


    def query_task_info(self, instance_ids: list[str]):
        result = {}
        current_result = None
        for instance_id in instance_ids:
            try:
                current_result = self.execute_sql_query(instance_id)
            except Exception as e:
                logger.warning("instance_id: {}, query job result error: {}", instance_id, str(e))
            if current_result:
                result[instance_id] = current_result
        return result

    def execute_sql_query(self, instance_id):
        result = None
        create_tables_sql = str(self.sql_dict.get("create_tables_sql"))
        query_sql = str(self.sql_dict.get("query_sql"))
        with SQLManager.create_connect() as conn:
            conn.execute(text(create_tables_sql))
            execute_result = conn.execute(text(query_sql), {"instance_id": instance_id})
            result = execute_result.fetchall()
        return result

    # todo 删除接口待实现
    def delete_task_info(self, instance_id: str):
        create_tables_sql = self.sql_dict.get("create_tables_sql")
        delete_task_instance_sql = self.sql_dict.get("delete_task_instance_sql")
        try:
            with SQLManager.create_connect() as conn:
                conn.execute(text(create_tables_sql))
                conn.execute(text(delete_task_instance_sql), {"instance_id": instance_id})
        except Exception as e:
            logger.warning(f"delete database for flow: {instance_id}", e)

    def delete_task_operate_info(self, instance_id: str):
        create_duplicate_img_tables_sql = self.sql_dict.get("create_duplicate_img_tables_sql")
        create_similar_img_tables_sql = self.sql_dict.get("create_similar_img_tables_sql")
        create_similar_text_tables_sql = self.sql_dict.get("create_similar_text_tables_sql")
        delete_duplicate_img_tables_sql = self.sql_dict.get("delete_duplicate_img_tables_sql")
        delete_similar_img_tables_sql = self.sql_dict.get("delete_similar_img_tables_sql")
        delete_similar_text_tables_sql = self.sql_dict.get("delete_similar_text_tables_sql")
        try:
            with SQLManager.create_connect() as conn:
                conn.execute(text(create_duplicate_img_tables_sql))
                conn.execute(text(delete_duplicate_img_tables_sql), {"instance_id": instance_id})
                conn.execute(text(create_similar_img_tables_sql))
                conn.execute(text(delete_similar_img_tables_sql), {"instance_id": instance_id})
                conn.execute(text(create_similar_text_tables_sql))
                conn.execute(text(delete_similar_text_tables_sql), {"instance_id": instance_id})
        except Exception as e:
            logger.warning(f"delete database for flow: {instance_id} error", e)
