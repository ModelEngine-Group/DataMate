from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

from app.module.system.service.log_pvc_monitor import DiskUsage, LogPvcMonitor


def _write_file(path: Path, mtime: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(path.name, encoding="utf-8")
    os.utime(path, (mtime, mtime))
    return path


def _disk_usage_sequence(ratios: Iterable[float]):
    iterator = iter(ratios)
    last_ratio = 0.0

    def disk_usage(_path: Path) -> DiskUsage:
        nonlocal last_ratio
        try:
            last_ratio = next(iterator)
        except StopIteration:
            pass
        total = 1000
        used = int(total * last_ratio)
        return DiskUsage(total=total, used=used, free=total - used)

    return disk_usage


def test_cleanup_skips_when_usage_below_threshold(tmp_path: Path) -> None:
    log_file = _write_file(tmp_path / "old.log", 1)
    monitor = LogPvcMonitor(
        root_path=tmp_path,
        threshold=0.9,
        delete_batch_size=10,
        file_suffixes="log,out,err",
        disk_usage=_disk_usage_sequence([0.5]),
    )

    assert monitor.cleanup_if_needed() == 0
    assert log_file.exists()


def test_cleanup_deletes_only_configured_suffixes_case_insensitive(tmp_path: Path) -> None:
    deleted_files = [
        _write_file(tmp_path / "a.log", 1),
        _write_file(tmp_path / "b.out", 2),
        _write_file(tmp_path / "c.err", 3),
        _write_file(tmp_path / "d.LOG", 4),
    ]
    kept_files = [
        _write_file(tmp_path / "e.txt", 5),
        _write_file(tmp_path / "f.log.bak", 6),
    ]
    monitor = LogPvcMonitor(
        root_path=tmp_path,
        threshold=0.9,
        delete_batch_size=10,
        file_suffixes="log,out,err",
        disk_usage=_disk_usage_sequence([0.95, 0.5]),
    )

    assert monitor.cleanup_if_needed() == len(deleted_files)
    assert all(not path.exists() for path in deleted_files)
    assert all(path.exists() for path in kept_files)


def test_cleanup_deletes_oldest_ten_files_by_mtime(tmp_path: Path) -> None:
    files = [_write_file(tmp_path / f"{index:02d}.log", index) for index in range(12)]
    monitor = LogPvcMonitor(
        root_path=tmp_path,
        threshold=0.9,
        delete_batch_size=10,
        file_suffixes="log,out,err",
        disk_usage=_disk_usage_sequence([0.95, 0.5]),
    )

    assert monitor.cleanup_if_needed() == 10
    assert all(not path.exists() for path in files[:10])
    assert all(path.exists() for path in files[10:])


def test_cleanup_continues_batches_until_usage_below_threshold(tmp_path: Path) -> None:
    files = [_write_file(tmp_path / f"{index:02d}.err", index) for index in range(25)]
    monitor = LogPvcMonitor(
        root_path=tmp_path,
        threshold=0.9,
        delete_batch_size=10,
        file_suffixes="log,out,err",
        disk_usage=_disk_usage_sequence([0.95, 0.94, 0.5]),
    )

    assert monitor.cleanup_if_needed() == 20
    assert all(not path.exists() for path in files[:20])
    assert all(path.exists() for path in files[20:])


def test_cleanup_skips_directory_symlink_missing_and_failed_files(tmp_path: Path) -> None:
    directory = tmp_path / "dir.log"
    directory.mkdir()
    target = _write_file(tmp_path / "target.txt", 1)
    symlink = tmp_path / "link.log"
    symlink.symlink_to(target)
    missing = _write_file(tmp_path / "missing.log", 2)
    failed = _write_file(tmp_path / "failed.err", 3)
    deleted = _write_file(tmp_path / "deleted.out", 4)

    def unlink_file(path: Path) -> None:
        if path == missing:
            path.unlink()
            raise FileNotFoundError(path)
        if path == failed:
            raise OSError("permission denied")
        path.unlink()

    monitor = LogPvcMonitor(
        root_path=tmp_path,
        threshold=0.9,
        delete_batch_size=10,
        file_suffixes="log,out,err",
        disk_usage=_disk_usage_sequence([0.95, 0.5]),
        unlink_file=unlink_file,
    )

    assert monitor.cleanup_if_needed() == 1
    assert directory.exists()
    assert symlink.exists()
    assert target.exists()
    assert not missing.exists()
    assert failed.exists()
    assert not deleted.exists()
