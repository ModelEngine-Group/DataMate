#!/usr/bin/env python3
"""Run WeNet recognition from the DataMate runtime environment."""

import sys


def main() -> None:
    try:
        from wenet.bin.recognize import main as wenet_main  # type: ignore
    except ImportError as exc:
        print(
            "[ERROR] Cannot import WeNet from the runtime environment. "
            "Install the pinned WeNet package/source listed in audio_runtime_dependencies.md.",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    wenet_main()


if __name__ == "__main__":
    main()
