import logging
import sys
from pathlib import Path
from app.core.config import settings

def setup_logging():
    """配置应用程序日志"""
    
    # 创建logs目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 配置日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 创建处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    file_handler = logging.FileHandler(
        log_dir / "app.log",
        encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    error_handler = logging.FileHandler(
        log_dir / "error.log", 
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    
    # 设置格式
    formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # 配置第三方库日志级别（减少详细日志）
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)  # 隐藏SQL查询日志
    logging.getLogger("httpx").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器"""
    return logging.getLogger(name)