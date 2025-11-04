import logging
import sys
from pathlib import Path
from app.core.config import settings

class CenteredLevelNameFormatter(logging.Formatter):
    """Center the level name in the log output"""
    
    def format(self, record):
        # 将 levelname 居中对齐到8个字符
        record.levelname = record.levelname.center(8)
        return super().format(record)

def setup_logging():
    
    log_format = "%(asctime)s [%(levelname)s] - %(name)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    log_dir = Path(settings.log_file_dir)
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(
        log_dir / "python-backend.log",
        encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Style setting - Centered level names
    formatter = CenteredLevelNameFormatter(log_format, date_format)
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(file_handler)
    
    # Uvicorn
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers.clear()
    uvicorn_logger.addHandler(console_handler)
    uvicorn_logger.setLevel(logging.INFO)
    
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers.clear()
    uvicorn_access.addHandler(console_handler)
    uvicorn_access.setLevel(logging.DEBUG)
    
    uvicorn_error = logging.getLogger("uvicorn.error")
    uvicorn_error.handlers.clear()
    uvicorn_error.addHandler(console_handler)
    uvicorn_error.setLevel(logging.ERROR)
    
    # SQLAlchemy (ERROR only)
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.setLevel(logging.ERROR)
    sqlalchemy_logger.addHandler(console_handler)
    sqlalchemy_logger.setLevel(logging.ERROR)

    # Minimize noise from HTTPX and HTTPCore
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("httpcore").setLevel(logging.ERROR)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)