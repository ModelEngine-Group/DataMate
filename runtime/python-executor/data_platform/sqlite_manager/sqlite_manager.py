# -- encoding: utf-8 --

import time
from random import uniform

import sqlite3
from loguru import logger


class SQLiteManager:

    @staticmethod
    def create_connect(db_path: str, max_retries=5, base_delay=1):
        """
        连接到 Sqlite 数据库。
        :return: 返回连接对象。
        """
        if db_path is None or db_path == "":
            raise ValueError("db_path cannot be empty. Please provide a valid database path.")
        attempt = 0

        while True:
            try:
                conn = sqlite3.connect(db_path)
                break
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed with error: {str(e)}")
                if attempt >= max_retries - 1:
                    raise
                wait_time = min(30, base_delay * (2 ** attempt))  # 不超过30秒的最大延时
                jitter = uniform(-wait_time / 4, wait_time / 4)  # 增加随机抖动因子
                time.sleep(wait_time + jitter)
                attempt += 1
        return conn
