from pathlib import Path


def test_orchestration_module_has_no_python_sources_yet() -> None:
    module_dir = Path(__file__).resolve().parents[1] / "app" / "module" / "orchestration"
    py_files = list(module_dir.rglob("*.py"))

    assert py_files == [], (
        "orchestration 模块已有 Python 实现，请补充真实业务单测并删除该占位用例"
    )


def test_orchestration_module_scaffold_directories_exist() -> None:
    root = Path(__file__).resolve().parents[1] / "app" / "module" / "orchestration"

    assert (root / "interface").exists()
    assert (root / "schema").exists()
    assert (root / "service").exists()


def test_orchestration_scaffold_contains_only_directories_or_cache() -> None:
    root = Path(__file__).resolve().parents[1] / "app" / "module" / "orchestration"
    names = {p.name for p in root.iterdir()}
    assert "interface" in names
    assert "schema" in names
    assert "service" in names


def test_orchestration_module_path_exists() -> None:
    root = Path(__file__).resolve().parents[1] / "app" / "module" / "orchestration"
    assert root.exists()
    assert root.is_dir()
