# -*- coding: utf-8 -*-
import importlib.abc
import importlib.util
from pathlib import Path


class CustomImporter(importlib.abc.MetaPathFinder):
    def __init__(self, base_path):
        self.base_path = Path(base_path).resolve()

    def find_spec(self, fullname, path, target=None):
        # 将模块名转换为路径（例如：mypkg.mymodule -> mypkg/mymodule.py）
        parts = fullname.split(".")
        module_path = self.base_path.joinpath(*parts)

        # 检查是否存在 .py 文件或目录
        if module_path.with_suffix(".py").exists():
            return importlib.util.spec_from_file_location(
                fullname,
                str(module_path.with_suffix(".py")),
                submodule_search_locations=[str(module_path.parent)]
            )
        elif module_path.is_dir() and (module_path / "__init__.py").exists():
            return importlib.util.spec_from_file_location(
                fullname,
                str(module_path / "__init__.py"),
                submodule_search_locations=[str(module_path)]
            )
        else:
            return None
