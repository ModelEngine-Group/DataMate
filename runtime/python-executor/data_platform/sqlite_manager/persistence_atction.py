# -*- coding: utf-8 -*-

import json
import time
import os
from pathlib import Path
from typing import Dict, Any

from loguru import logger

from data_platform.sqlite_manager.sqlite_manager import SQLiteManager


def delete_task_info(instance_id: str):
    db_path = f"/flow/{instance_id}.db"
    try:
        os.remove(db_path)
    except Exception as e:
        logger.warning(f"delete database for flow：{instance_id} error", e)


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
        meta_file_id = str(sample.get("sourceFileId"))
        meta_file_size = str(sample.get("sourceFileSize"))
        file_id = str(sample.get("fileId"))
        file_size = str(sample.get("fileSize"))
        file_type = str(sample.get("fileType"))
        file_name = str(sample.get("fileName"))
        file_path = str(sample.get("filePath"))
        source_file_modify_time = int(sample.get("sourceFileModifyTime") if sample.get("sourceFileModifyTime") else "0")
        status = int(sample.get("execute_status"))
        failed_reason = sample.get("failed_reason")
        operator_id = str(failed_reason.get("op_name")) if failed_reason else ""
        error_code = str(failed_reason.get("error_code")) if failed_reason else ""
        incremental = str(sample.get("incremental") if sample.get("incremental") else '')
        child_id = sample.get("childId")
        slice_num = sample.get('slice_num', 0)
        insert_data = [instance_id, meta_file_name, meta_file_type, meta_file_id, meta_file_size, file_id, file_size,
                       file_type, file_name, file_path, source_file_modify_time, status, operator_id, error_code,
                       incremental, child_id, slice_num]
        self.insert_clean_result(insert_data, instance_id)

    def insert_clean_result(self, insert_data, instance_id):
        retries = 0
        max_retries = 20
        retry_delay = 1
        while retries <= max_retries:
            db_path = f"/flow/{instance_id}.db"
            try:
                insert_sql = str(self.sql_dict.get("insert_sql"))
                create_tables_sql = str(self.sql_dict.get("create_tables_sql"))
                with SQLiteManager.create_connect(db_path) as conn:
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute(create_tables_sql)
                    conn.execute(insert_sql, insert_data)
                    return
            except Exception as e:
                if "database is locked" in str(e) or "locking protocol" in str(e):
                    logger.warning("db_path: {}, database is locked: {}", db_path, str(e))
                    retries += 1
                    time.sleep(retry_delay)
                else:
                    logger.error("db_path: {}, database execute failed: {}", db_path, str(e))
                    raise RuntimeError(82000, str(e)) from None
        raise Exception("Max retries exceeded")

    def query_task_info(self, instance_ids: list[str]):
        result = {}
        create_tables_sql = self.sql_dict.get("create_tables_sql")
        query_sql = self.sql_dict.get("query_sql")
        current_result = None
        for instance_id in instance_ids:
            db_path = f"/flow/{instance_id}.db"
            try:
                with SQLiteManager.create_connect(db_path) as conn:
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute(create_tables_sql)
                    cursor = conn.execute(query_sql, [instance_id])
                    current_result = cursor.fetchall()
            except Exception as e:
                logger.warning("instance_id: {}, query job result error: {}", instance_id, str(e))
            if current_result:
                result[instance_id] = current_result
        return result
