# -- encoding: utf-8 --
import os
import time
from random import uniform

from loguru import logger
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL


class SQLManager:

    @staticmethod
    def create_connect(max_retries=5, base_delay=1):
        """
        连接到 MySQL 数据库，使用 SQLAlchemy 和 PyMySQL。
        :param max_retries: 最大重试次数
        :param base_delay: 基础时延
        :return: 返回 SQLAlchemy 连接对象
        """

        connection_url = URL.create(
            drivername="postgresql+psycopg2",  # 核心修改：使用 pg 驱动
            username=os.getenv("PG_USER", "postgres"), # 建议修改环境变量名
            password=os.getenv("PG_PASSWORD", "password"),
            host=os.getenv("PG_HOST", "datamate-database"),
            port=int(os.getenv("PG_PORT", 5432)), # 修改默认端口为 5432
            database=os.getenv("PG_DATABASE", "datamate"),
        )

        attempt = 0

        while True:
            try:
                engine = create_engine(connection_url, pool_pre_ping=True, isolation_level="AUTOCOMMIT")
                return engine.connect()
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed with error: {str(e)}")
                if attempt >= max_retries - 1:
                    raise
                wait_time = min(30, base_delay * (2 ** attempt))  # 不超过30秒的最大延时
                jitter = uniform(-wait_time / 4, wait_time / 4)  # 增加随机抖动因子
                time.sleep(wait_time + jitter)
                attempt += 1


if __name__ == "__main__":
    with SQLManager.create_connect() as connection:
      inspector = inspect(connection)
      print(inspector.get_table_names())

