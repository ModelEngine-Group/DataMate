from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional

class Settings(BaseSettings):
    """应用程序配置"""

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = 'ignore'

    # Service
    app_name: str = "DataMate Python Backend"
    app_version: str = "1.0.0"
    app_description: str = "Adapter for integrating Data Management System with Label Studio"

    host: str = "0.0.0.0"
    port: int = 18000

    # CORS
    # allowed_origins: List[str] = ["*"]
    # allowed_methods: List[str] = ["*"]
    # allowed_headers: List[str] = ["*"]

    # Log
    log_level: str = "INFO"
    debug: bool = True
    log_file_dir: str = "/var/log/datamate/backend-python"
    rag_storage_dir: str = "/data/rag_storage"

    # Database
    pgsql_host: str = "datamate-database"
    pgsql_port: int = 5432
    pgsql_user: str = "postgres"
    pgsql_password: str = "password"
    pgsql_database: str = "datamate"

    # Database
    mysql_host: str = "datamate-database"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "password"
    mysql_database: str = "datamate"

    database_url: str = ""  # Will be overridden by build_database_url() if not provided

    @model_validator(mode='after')
    def build_database_url(self):
        """如果没有提供 database_url，则根据 MySQL 配置构建"""
        if not self.database_url:
            if self.pgsql_host:
                if self.pgsql_password and self.pgsql_user:
                    self.database_url = f"postgresql+asyncpg://{self.pgsql_user}:{self.pgsql_password}@{self.pgsql_host}:{self.pgsql_port}/{self.pgsql_database}"
                else:
                    self.database_url = f"postgresql+asyncpg://{self.pgsql_host}:{self.pgsql_port}/{self.pgsql_database}"
            elif self.mysql_password and self.mysql_user:
                self.database_url = f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            else:
                self.database_url = f"mysql+aiomysql://{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        return self


    # Label Studio
    label_studio_base_url: str = "http://label-studio:8000"
    label_studio_username: Optional[str] = "admin@demo.com"
    label_studio_password: Optional[str] = "demoadmin"
    label_studio_user_token: Optional[str] = "abc123abc123"  # Legacy Token

    label_studio_local_document_root: str = "/label-studio/local"  # Label Studio local file storage path
    label_studio_file_path_prefix: str = "/data/local-files/?d="  # Label Studio local file serving URL prefix

    ls_task_page_size: int = 1000

    # DataMate
    dm_file_path_prefix: str = "/dataset"  # DM存储文件夹前缀

    datamate_jwt_enable: bool = False

# 全局设置实例
settings = Settings()
