from __future__ import annotations

import logging
import os
import subprocess
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings
from app.core.logging import setup_logging


def _remove_datamate_handlers(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        if getattr(handler, "_datamate_managed", False):
            logger.removeHandler(handler)
            handler.close()


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts/images/common/log-rotate-copytruncate.sh").exists():
            return parent
    raise RuntimeError("repo root not found")


def test_setup_logging_uses_rotating_file_handler_without_duplicates(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "log_file_dir", str(tmp_path))
    monkeypatch.setattr(settings, "log_rotation_max_size", "1MB")
    monkeypatch.setattr(settings, "log_rotation_backup_count", 7)

    root_logger = logging.getLogger()
    try:
        setup_logging()
        setup_logging()

        file_handlers = [
            handler
            for handler in root_logger.handlers
            if getattr(handler, "_datamate_managed", False)
            and isinstance(handler, RotatingFileHandler)
        ]
        assert len(file_handlers) == 1
        assert file_handlers[0].maxBytes == 1024 * 1024
        assert file_handlers[0].backupCount == 7
        assert file_handlers[0].namer(str(tmp_path / "python-backend.log.1")).endswith(
            "python-backend.1.log"
        )
    finally:
        _remove_datamate_handlers(root_logger)
        _remove_datamate_handlers(logging.getLogger("uvicorn"))
        _remove_datamate_handlers(logging.getLogger("uvicorn.access"))
        _remove_datamate_handlers(logging.getLogger("uvicorn.error"))
        _remove_datamate_handlers(logging.getLogger("sqlalchemy.engine"))


def test_copytruncate_log_rotation_script_rotates_only_log_like_files(tmp_path: Path) -> None:
    log_file = tmp_path / "worker.log"
    old_backup = tmp_path / "worker.1.log"
    ignored_file = tmp_path / "worker.txt"

    log_file.write_text("x" * 20, encoding="utf-8")
    old_backup.write_text("old", encoding="utf-8")
    ignored_file.write_text("x" * 20, encoding="utf-8")

    env = {
        **os.environ,
        "LOG_ROTATION_MAX_SIZE": "10B",
        "LOG_ROTATION_BACKUP_COUNT": "2",
    }
    subprocess.run(
        [
            "bash",
            str(_repo_root() / "scripts/images/common/log-rotate-copytruncate.sh"),
            "--once",
            str(tmp_path),
        ],
        check=True,
        env=env,
    )

    assert log_file.read_text(encoding="utf-8") == ""
    assert (tmp_path / "worker.1.log").read_text(encoding="utf-8") == "x" * 20
    assert (tmp_path / "worker.2.log").read_text(encoding="utf-8") == "old"
    assert ignored_file.read_text(encoding="utf-8") == "x" * 20


def test_log_rotation_shell_scripts_are_valid_bash() -> None:
    root = _repo_root()
    scripts = [
        root / "scripts/images/common/log-rotate-copytruncate.sh",
        root / "scripts/images/frontend/rotate-nginx-logs.sh",
        root / "scripts/images/database/prune-postgres-logs.sh",
        root / "scripts/images/database/start.sh",
    ]
    for script in scripts:
        subprocess.run(["bash", "-n", str(script)], check=True)
