from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional, List
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

    # 日志配置
    log_level: str = "INFO"
    debug: bool = True
    log_file_dir: str = "/var/log/datamate"

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS配置
    # allowed_origins: List[str] = ["*"]
    # allowed_methods: List[str] = ["*"]
    # allowed_headers: List[str] = ["*"]

    # MySQL数据库配置 (优先级1)
    mysql_host: str = "datamate-database"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "password"
    mysql_database: str = "datamate"

    # 直接数据库URL配置（如果提供，将覆盖上述配置）
    # 初始值为空字符串，在 model_validator 中会被设置为完整的 URL
    database_url: str = ""
    
    @model_validator(mode='after')
    def build_database_url(self):
        """如果没有提供 database_url，则根据 MySQL 配置构建"""
        if not self.database_url:
            if self.mysql_password and self.mysql_user:
                self.database_url = f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            else:
                self.database_url = f"mysql+aiomysql://{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        return self


    # =========================
    # Label Studio 服务配置
    # =========================
    label_studio_base_url: str = "http://label-studio:8000"
    label_studio_username: Optional[str] = "admin@demo.com"  # Label Studio 用户名（用于登录）
    label_studio_password: Optional[str] = "demoadmin"  # Label Studio 密码（用于登录）
    label_studio_user_token: Optional[str] = "abc123abc123"  # Legacy Token

    label_studio_local_storage_dataset_base_path: str = "/label-studio/local"  # Label Studio容器中的本地存储基础路径
    label_studio_file_path_prefix: str = "/data/local-files/?d="  # Label Studio本地文件服务路径前缀

    ls_task_page_size: int = 1000

    # =========================
    # Data Management 服务配置
    # =========================
    dm_file_path_prefix: str = "/dataset"  # DM存储文件夹前缀

# 全局设置实例
settings = Settings()
