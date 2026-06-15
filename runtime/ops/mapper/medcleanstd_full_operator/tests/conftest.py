from __future__ import annotations

import sys
from pathlib import Path


OPERATOR_ROOT = Path(__file__).resolve().parents[1]
if str(OPERATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(OPERATOR_ROOT))

RUNTIME_DIR = OPERATOR_ROOT.parents[3]
PYTHON_EXECUTOR_DIR = RUNTIME_DIR / "python-executor"
if PYTHON_EXECUTOR_DIR.exists() and str(PYTHON_EXECUTOR_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_EXECUTOR_DIR))
