# -- encoding: utf-8 --
import os
import time
from random import uniform
from threading import Lock

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


class SQLManager:
    _engine = None
    _lock = Lock()  # 确保多线程环境下只创建一个引擎

    @classmethod
    def _get_engine(cls):
        """
        单例模式获取 Engine，确保全局只有一个连接池
        """
        if cls._engine is not None:
            return cls._engine

        with cls._lock:
            if cls._engine is not None:
                return cls._engine

            # 构建连接 URL
            connection_url = URL.create(
                drivername="postgresql+psycopg2",
                username=os.getenv("PG_USER", "postgres"),
                password=os.getenv("PG_PASSWORD", "password"),
                host=os.getenv("PG_HOST", "datamate-database"),
                port=int(os.getenv("PG_PORT", 5432)),
                database=os.getenv("PG_DATABASE", "datamate"),
            )

            # 创建引擎 (只执行一次)
            # 注意：AUTOCOMMIT 虽然方便，但建议根据业务场景谨慎使用。
            # 如果需要事务控制（比如两张表必须同时更新成功），AUTOCOMMIT 会导致无法回滚。
            cls._engine = create_engine(
                connection_url,
                pool_pre_ping=True,
                isolation_level="AUTOCOMMIT",
                pool_size=5,       # 显式指定池大小
                max_overflow=15,   # 显式指定溢出
                pool_timeout=30,
                pool_recycle=1800  # 10分钟回收连接
            )
            logger.info("Database Engine initialized successfully.")
            return cls._engine

    @staticmethod
    def create_connect(max_retries=5, base_delay=1):
        """
        从现有的 Engine 连接池中获取连接，包含重试逻辑
        """
        attempt = 0
        while True:
            try:
                # 1. 获取全局引擎
                engine = SQLManager._get_engine()
                # 2. 从池中借出一个连接
                return engine.connect()
            except Exception as e:
                attempt += 1
                logger.error(f"Connection attempt {attempt} failed: {str(e)}")

                if attempt >= max_retries:
                    logger.error("Max retries reached. Could not connect to database.")
                    raise

                # 重试等待逻辑
                wait_time = min(30, base_delay * (2 ** (attempt - 1)))
                jitter = uniform(-wait_time / 4, wait_time / 4)
                sleep_time = wait_time + jitter
                logger.info(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
