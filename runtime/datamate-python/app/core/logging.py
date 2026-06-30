import logging
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings

_SIZE_PATTERN = re.compile(r"^\s*(\d+)\s*([KMG]?B?)?\s*$", re.IGNORECASE)


class CenteredLevelNameFormatter(logging.Formatter):
    """Center the level name in the log output"""
    
    def format(self, record):
        # 将 levelname 居中对齐到8个字符
        record.levelname = record.levelname.center(8)
        return super().format(record)


def _parse_size_to_bytes(value: str) -> int:
    match = _SIZE_PATTERN.match(value)
    if not match:
        return 100 * 1024 * 1024

    amount = int(match.group(1))
    unit = (match.group(2) or "B").upper()
    if unit in {"G", "GB"}:
        return amount * 1024 * 1024 * 1024
    if unit in {"M", "MB"}:
        return amount * 1024 * 1024
    if unit in {"K", "KB"}:
        return amount * 1024
    return amount


def _rotated_log_namer(default_name: str) -> str:
    path = Path(default_name)
    index_suffix = path.suffix
    if not index_suffix.lstrip(".").isdigit():
        return default_name

    base_path = Path(str(path)[: -len(index_suffix)])
    if not base_path.suffix:
        return default_name

    return str(base_path.with_name(f"{base_path.stem}{index_suffix}{base_path.suffix}"))


def _remove_managed_handlers(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        if getattr(handler, "_datamate_managed", False):
            logger.removeHandler(handler)
            handler.close()


def _mark_managed(handler: logging.Handler) -> logging.Handler:
    setattr(handler, "_datamate_managed", True)
    return handler


def setup_logging():
    
    log_format = "%(asctime)s [%(levelname)s] - %(name)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    console_handler = _mark_managed(logging.StreamHandler(sys.stdout))
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    log_dir = Path(settings.log_file_dir)
    log_dir.mkdir(exist_ok=True)
    file_handler = _mark_managed(RotatingFileHandler(
        log_dir / "python-backend.log",
        maxBytes=_parse_size_to_bytes(settings.log_rotation_max_size),
        backupCount=max(1, settings.log_rotation_backup_count),
        encoding="utf-8"
    ))
    file_handler.namer = _rotated_log_namer
    file_handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Style setting - Centered level names
    formatter = CenteredLevelNameFormatter(log_format, date_format)
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Root Logger
    root_logger = logging.getLogger()
    _remove_managed_handlers(root_logger)
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    root_logger.addHandler(console_handler)
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
    _remove_managed_handlers(sqlalchemy_logger)
    sqlalchemy_logger.setLevel(logging.ERROR)
    sqlalchemy_logger.addHandler(console_handler)
    sqlalchemy_logger.setLevel(logging.ERROR)

    # Minimize noise from HTTPX and HTTPCore
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("httpcore").setLevel(logging.ERROR)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
