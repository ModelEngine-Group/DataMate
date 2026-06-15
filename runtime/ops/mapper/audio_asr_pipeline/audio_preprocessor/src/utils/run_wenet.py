#!/usr/bin/env python3
"""Run WeNet recognition with DataMate external dependency lookup."""

import os
import sys
from pathlib import Path


def _prepend_existing_path(path: Path) -> None:
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))


def _configure_wenet_path() -> None:
    local_libs = Path(__file__).resolve().parents[2] / "local_libs"
    ops_site = Path(os.environ.get("DATAMATE_OPS_SITE_PACKAGES", "/usr/local/lib/ops/site-packages"))
    _prepend_existing_path(ops_site)
    _prepend_existing_path(local_libs)


def main() -> None:
    _configure_wenet_path()
    try:
        from wenet.bin.recognize import main as wenet_main  # type: ignore
    except ImportError as exc:
        print(
            "[ERROR] Cannot import WeNet. Checked DATAMATE_OPS_SITE_PACKAGES, "
            "/usr/local/lib/ops/site-packages, packaged local_libs, and the current Python environment.",
            file=sys.stderr,
        )
        print(f"[ERROR] import detail: {exc}", file=sys.stderr)
        print(f"[INFO] Python path: {sys.path}", file=sys.stderr)
        raise SystemExit(1) from exc
    wenet_main()


if __name__ == "__main__":
    main()
