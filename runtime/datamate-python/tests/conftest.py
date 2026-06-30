from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType


def _register_namespace(module_name: str, module_path: Path) -> None:
    namespace_pkg = ModuleType(module_name)
    namespace_pkg.__path__ = [str(module_path)]  # type: ignore[attr-defined]
    sys.modules.setdefault(module_name, namespace_pkg)


def pytest_sessionstart(session) -> None:
    """避免测试导入 app.module.* 时触发 app/module/__init__.py 的重依赖加载。"""
    root = Path(__file__).resolve().parents[1] / "app" / "module"

    _register_namespace("app.module", root)
    _register_namespace("app.module.cleaning", root / "cleaning")
    _register_namespace("app.module.cleaning.service", root / "cleaning" / "service")
    _register_namespace("app.module.rag", root / "rag")
    _register_namespace("app.module.rag.service", root / "rag" / "service")
    _register_namespace("app.module.rag.service.common", root / "rag" / "service" / "common")
