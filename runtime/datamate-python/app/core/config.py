from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """应用程序配置"""

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = 'ignore'  # 允许额外字段（如 Shell 脚本专用的环境变量）

    # =========================
    # Adapter 服务配置
    # =========================
    app_name: str = "Label Studio Adapter"
    app_version: str = "1.0.0"
    app_description: str = "Adapter for integrating Data Management System with Label Studio"
    debug: bool = True

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS配置
    allowed_origins: list = ["*"]
    allowed_methods: list = ["*"]
    allowed_headers: list = ["*"]

    # MySQL数据库配置 (优先级1)
    mysql_host: Optional[str] = None
    mysql_port: int = 3306
    mysql_user: Optional[str] = None
    mysql_password: Optional[str] = None
    mysql_database: Optional[str] = None

    # PostgreSQL数据库配置 (优先级2)
    postgres_host: Optional[str] = None
    postgres_port: int = 5432
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_database: Optional[str] = None

    # SQLite数据库配置 (优先级3 - 兜底)
    sqlite_path: str = "data/labelstudio_adapter.db"

    # 直接数据库URL配置（如果提供，将覆盖上述配置）
    database_url: Optional[str] = None

    # 日志配置
    log_level: str = "INFO"

    # 安全配置
    secret_key: str = "your-secret-key-change-this-in-production"
    access_token_expire_minutes: int = 30

    # =========================
    # Label Studio 服务配置
    # =========================
    label_studio_base_url: str = "http://label-studio:8080"
    label_studio_username: Optional[str] = None  # Label Studio 用户名（用于登录）
    label_studio_password: Optional[str] = None  # Label Studio 密码（用于登录）
    label_studio_user_token: Optional[str] = None  # Legacy Token

    label_studio_local_storage_dataset_base_path: str = "/label-studio/local_files/dataset"  # Label Studio容器中的本地存储基础路径
    label_studio_local_storage_upload_base_path: str = "/label-studio/local_files/upload"  # Label Studio容器中的本地存储基础路径
    label_studio_file_path_prefix: str = "/data/local-files/?d="  # Label Studio本地文件服务路径前缀

    ls_task_page_size: int = 1000


    # =========================
    # Data Management 服务配置
    # =========================
    dm_file_path_prefix: str = "/"  # DM存储文件夹前缀


    @property
    def computed_database_url(self) -> str:
        """
        根据优先级自动选择数据库连接URL
        优先级：MySQL > PostgreSQL > SQLite3
        """
        # 如果直接提供了database_url，优先使用
        if self.database_url:
            return self.database_url

        # 优先级1: MySQL
        if all([self.mysql_host, self.mysql_user, self.mysql_password, self.mysql_database]):
            return f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"

        # 优先级2: PostgreSQL
        if all([self.postgres_host, self.postgres_user, self.postgres_password, self.postgres_database]):
            return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"

        # 优先级3: SQLite (兜底)
        sqlite_full_path = Path(self.sqlite_path).absolute()
        # 确保目录存在
        sqlite_full_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{sqlite_full_path}"

    @property
    def sync_database_url(self) -> str:
        """
        用于数据库迁移的同步连接URL
        将异步驱动替换为同步驱动
        """
        async_url = self.computed_database_url

        # 替换异步驱动为同步驱动
        sync_replacements = {
            "mysql+aiomysql://": "mysql+pymysql://",
            "postgresql+asyncpg://": "postgresql+psycopg2://",
            "sqlite+aiosqlite:///": "sqlite:///"
        }

        for async_driver, sync_driver in sync_replacements.items():
            if async_url.startswith(async_driver):
                return async_url.replace(async_driver, sync_driver)

        return async_url

    def get_database_info(self) -> dict:
        """获取数据库配置信息"""
        url = self.computed_database_url

        if url.startswith("mysql"):
            db_type = "MySQL"
        elif url.startswith("postgresql"):
            db_type = "PostgreSQL"
        elif url.startswith("sqlite"):
            db_type = "SQLite"
        else:
            db_type = "Unknown"

        return {
            "type": db_type,
            "url": url,
            "sync_url": self.sync_database_url
        }


# 全局设置实例
settings = Settings()
