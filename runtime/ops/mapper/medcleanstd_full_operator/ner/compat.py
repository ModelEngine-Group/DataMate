from __future__ import annotations

import ast
import hashlib
import os
import sys
import types


def _install_simplejson_shim() -> None:
    try:
        import simplejson  # noqa: F401
    except ModuleNotFoundError:
        import json as _json

        sys.modules["simplejson"] = _json


def _install_sortedcontainers_shim() -> None:
    try:
        import sortedcontainers  # noqa: F401
    except ModuleNotFoundError:
        module = types.ModuleType("sortedcontainers")

        class SortedList(list):
            def __init__(self, iterable=None, key=None):
                self._key = key or (lambda value: value)
                values = list(iterable) if iterable is not None else []
                values.sort(key=self._key)
                super().__init__(values)

            def add(self, value):
                super().append(value)
                super().sort(key=self._key)

        module.SortedList = SortedList
        sys.modules["sortedcontainers"] = module


def _install_addict_shim() -> None:
    try:
        import addict  # noqa: F401
    except ModuleNotFoundError:
        module = types.ModuleType("addict")

        class Dict(dict):
            def __init__(self, *args, **kwargs):
                super().__init__()
                self.update(*args, **kwargs)

            def __getattr__(self, item):
                try:
                    return self[item]
                except KeyError as exc:
                    raise AttributeError(item) from exc

            def __setattr__(self, key, value):
                self[key] = value

            def __delattr__(self, item):
                try:
                    del self[item]
                except KeyError as exc:
                    raise AttributeError(item) from exc

            def __setitem__(self, key, value):
                super().__setitem__(key, self._convert(value))

            def update(self, *args, **kwargs):
                for mapping in args:
                    if hasattr(mapping, "items"):
                        for k, v in mapping.items():
                            self[k] = v
                    else:
                        for k, v in mapping:
                            self[k] = v
                for k, v in kwargs.items():
                    self[k] = v

            @classmethod
            def _convert(cls, value):
                if isinstance(value, dict) and not isinstance(value, Dict):
                    return cls(value)
                if isinstance(value, list):
                    return [cls._convert(v) for v in value]
                return value

        module.Dict = Dict
        sys.modules["addict"] = module


def _install_oss2_shim() -> None:
    try:
        import oss2  # noqa: F401
    except ModuleNotFoundError:
        module = types.ModuleType("oss2")
        credentials_module = types.ModuleType("oss2.credentials")

        class CredentialsProvider:
            pass

        class ProviderAuthV4:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

        class ResumableDownloadStore:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

        class ResumableStore:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

        class Bucket:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

            def object_exists(self, *args, **kwargs):
                raise RuntimeError("oss2 shim: object_exists should not be called")

        class Credentials:
            def __init__(self, access_key_id=None, access_key_secret=None, security_token=None):
                self.access_key_id = access_key_id
                self.access_key_secret = access_key_secret
                self.security_token = security_token

        def resumable_download(*args, **kwargs):
            raise RuntimeError("oss2 shim: resumable_download should not be called")

        def resumable_upload(*args, **kwargs):
            raise RuntimeError("oss2 shim: resumable_upload should not be called")

        module.CredentialsProvider = CredentialsProvider
        module.ProviderAuthV4 = ProviderAuthV4
        module.ResumableDownloadStore = ResumableDownloadStore
        module.ResumableStore = ResumableStore
        module.Bucket = Bucket
        module.resumable_download = resumable_download
        module.resumable_upload = resumable_upload
        credentials_module.Credentials = Credentials

        sys.modules["oss2"] = module
        sys.modules["oss2.credentials"] = credentials_module


def _fallback_get_imports(filename: str) -> list[str]:
    with open(filename, encoding="utf-8") as f:
        content = f.read()

    imported_modules: set[str] = set()

    def _walk(node: ast.AST) -> None:
        if isinstance(node, ast.Try):
            return
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_module = alias.name.split(".")[0]
                if top_module:
                    imported_modules.add(top_module)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                top_module = node.module.split(".")[0]
                if top_module:
                    imported_modules.add(top_module)

        for child in ast.iter_child_nodes(node):
            _walk(child)

    _walk(ast.parse(content))
    return sorted(imported_modules)


def _install_datasets_load_shims() -> None:
    try:
        import datasets.load as datasets_load
    except Exception:
        return

    if not hasattr(datasets_load, "ALL_ALLOWED_EXTENSIONS"):
        try:
            from datasets.packaged_modules import _EXTENSION_TO_MODULE

            datasets_load.ALL_ALLOWED_EXTENSIONS = list(_EXTENSION_TO_MODULE.keys())
        except Exception:
            datasets_load.ALL_ALLOWED_EXTENSIONS = []

    if not hasattr(datasets_load, "files_to_hash"):
        def files_to_hash(paths):
            digest = hashlib.sha256()
            for path in paths:
                digest.update(str(path).encode("utf-8", "replace"))
                try:
                    stat_result = os.stat(path)
                    digest.update(str(stat_result.st_mtime_ns).encode("utf-8"))
                    digest.update(str(stat_result.st_size).encode("utf-8"))
                except Exception:
                    pass
            return digest.hexdigest()

        datasets_load.files_to_hash = files_to_hash

    class _DummyFactory:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def get_module(self, *args, **kwargs):
            raise RuntimeError(
                "datasets.load compatibility shim placeholder should not be used "
                "for local model pipeline"
            )

    def _dummy_function(*args, **kwargs):
        raise RuntimeError(
            "datasets.load compatibility shim placeholder should not be used "
            "for local model pipeline"
        )

    for name in (
        "HubDatasetModuleFactoryWithoutScript",
        "HubDatasetModuleFactoryWithScript",
        "LocalDatasetModuleFactoryWithoutScript",
        "LocalDatasetModuleFactoryWithScript",
    ):
        if not hasattr(datasets_load, name):
            setattr(datasets_load, name, _DummyFactory)

    for name in (
        "_get_importable_file_path",
        "resolve_trust_remote_code",
        "_create_importable_file",
        "_load_importable_file",
        "init_dynamic_modules",
    ):
        if not hasattr(datasets_load, name):
            setattr(datasets_load, name, _dummy_function)


def _install_datasets_get_imports_shim() -> None:
    try:
        import datasets.utils.py_utils as py_utils
    except Exception:
        return

    if hasattr(py_utils, "get_imports"):
        return

    try:
        from transformers.dynamic_module_utils import get_imports as hf_get_imports
    except Exception:
        hf_get_imports = _fallback_get_imports

    py_utils.get_imports = hf_get_imports


def _disable_modelscope_requirement_installs() -> None:
    try:
        import modelscope.utils.plugins as plugins
    except Exception:
        return

    def _skip_install_module_from_requirements(requirement_path):
        return None

    def _skip_install_requirements_by_files(requirements):
        return None

    plugins.install_module_from_requirements = _skip_install_module_from_requirements
    plugins.install_requirements_by_files = _skip_install_requirements_by_files


def install_compat_shims() -> None:
    _install_simplejson_shim()
    _install_sortedcontainers_shim()
    _install_addict_shim()
    _install_oss2_shim()
    _install_datasets_load_shims()
    _install_datasets_get_imports_shim()
    _disable_modelscope_requirement_installs()
