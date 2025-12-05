# -*- coding: utf-8 -*-

import json
import time
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from loguru import logger
from sqlalchemy import text

from datamate.sql_manager.sql_manager import SQLManager


class TaskInfoPersistence:
    def __init__(self):
        self.sql_dict = self.load_sql_dict()

    @staticmethod
    def load_sql_dict():
        """获取sql语句"""
        sql_config_path = str(Path(__file__).parent / 'sql' / 'sql_config.json')
        with open(sql_config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def update_task_result(self, sample, file_id = str(uuid.uuid4())):
        instance_id = str(sample.get("instance_id"))
        src_file_name = str(sample.get("sourceFileName"))
        src_file_type = str(sample.get("sourceFileType"))
        src_file_id = str(sample.get("sourceFileId"))
        src_file_size = int(sample.get("sourceFileSize"))

        file_size = str(sample.get("fileSize"))
        file_type = str(sample.get("fileType"))
        file_name = str(sample.get("fileName"))

        status = str(sample.get("execute_status"))
        failed_reason = str(sample.get("failed_reason"))
        result_data = {
            "instance_id": instance_id,
            "src_file_id": src_file_id,
            "dest_file_id": file_id,
            "src_name": src_file_name,
            "dest_name": file_name,
            "src_type": src_file_type,
            "dest_type": file_type,
            "src_size": src_file_size,
            "dest_size": file_size,
            "status": status,
            "result": failed_reason
        }
        self.insert_result(result_data, str(self.sql_dict.get("insert_clean_result_sql")))

    def update_file_result(self, sample, file_id):
        file_size = str(sample.get("fileSize"))
        file_type = str(sample.get("fileType"))
        file_name = str(sample.get("fileName"))
        dataset_id = str(sample.get("dataset_id"))
        file_path = str(sample.get("filePath"))
        create_time = datetime.now()
        last_access_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        file_data = {
            "id": file_id,
            "dataset_id": dataset_id,
            "file_name": file_name,
            "file_path": file_path,
            "file_type": file_type,
            "file_size": file_size,
            "status": "COMPLETED",
            "upload_time": create_time,
            "last_access_time": last_access_time,
            "created_at": create_time,
            "updated_at": create_time
        }
        self.insert_result(file_data, str(self.sql_dict.get("insert_dataset_file_sql")))

    def persistence_task_info(self, sample: Dict[str, Any]):
        file_id = str(uuid.uuid4())
        self.update_task_result(sample, file_id)
        self.update_file_result(sample, file_id)

    @staticmethod
    def insert_result(data, sql):
        retries = 0
        max_retries = 20
        retry_delay = 1
        while retries <= max_retries:
            try:
                with SQLManager.create_connect() as conn:
                    conn.execute(text(sql), data)
                return
            except Exception as e:
                if "database is locked" in str(e) or "locking protocol" in str(e):
                    retries += 1
                    time.sleep(retry_delay)
                else:
                    logger.error("database execute failed: {}", str(e))
                    raise RuntimeError(82000, str(e)) from None
        raise Exception("Max retries exceeded")

    def update_result(self, dataset_id, instance_id, status):
        dataset_data = {
            "dataset_id": dataset_id
        }
        query_dataset_sql = str(self.sql_dict.get("query_dataset_sql"))
        with SQLManager.create_connect() as conn:
            result = conn.execute(text(query_dataset_sql), dataset_data)
        if result:
            rows = result.fetchall()
            total_size = sum(int(row[0]) for row in rows)
            file_count = len(rows)
        else:
            total_size = 0
            file_count = 0

        dataset_data.update({
            "task_id": instance_id,
            "total_size": total_size,
            "file_count": file_count
        })

        update_dataset_sql = str(self.sql_dict.get("update_dataset_sql"))
        self.insert_result(dataset_data, update_dataset_sql)

        task_data = {
            "task_id": instance_id,
            "status": status,
            "total_size": total_size,
            "finished_time": datetime.now()
        }
        update_task_sql = str(self.sql_dict.get("update_task_sql"))
        self.insert_result(task_data, update_task_sql)

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
