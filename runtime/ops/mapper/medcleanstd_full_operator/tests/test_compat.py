from __future__ import annotations

import sys
import types

import pytest

from ner import compat


class TestCompatShims:
    def test_fallback_get_imports_ignores_try_block(self, tmp_path):
        source = tmp_path / "imports_sample.py"
        source.write_text(
            "import os\n"
            "try:\n"
            "    import hidden_module\n"
            "except Exception:\n"
            "    pass\n"
            "from json import dumps\n",
            encoding="utf-8",
        )

        imports = compat._fallback_get_imports(str(source))

        assert imports == ["json", "os"]

    def test_install_simple_sorted_addict_and_oss2_shims(self):
        compat._install_simplejson_shim()
        compat._install_sortedcontainers_shim()
        compat._install_addict_shim()
        compat._install_oss2_shim()

        import simplejson
        import sortedcontainers
        import addict
        import oss2

        assert simplejson.dumps({"a": 1}) == '{"a": 1}'

        values = sortedcontainers.SortedList([3, 1, 2])
        values.add(0)
        assert list(values) == [0, 1, 2, 3]

        payload = addict.Dict({"a": {"b": 1}})
        payload.c = 2
        assert payload.a.b == 1
        assert payload["c"] == 2

        assert hasattr(oss2, "Bucket")
        assert hasattr(oss2, "resumable_download")

    def test_install_compat_shims_on_fake_datasets_modules(self, monkeypatch: pytest.MonkeyPatch):
        datasets_pkg = types.ModuleType("datasets")
        datasets_load = types.ModuleType("datasets.load")
        datasets_packaged_modules = types.ModuleType("datasets.packaged_modules")
        datasets_packaged_modules._EXTENSION_TO_MODULE = {".txt": "text"}
        datasets_utils = types.ModuleType("datasets.utils")
        datasets_py_utils = types.ModuleType("datasets.utils.py_utils")

        transformers_pkg = types.ModuleType("transformers")
        dynamic_module_utils = types.ModuleType("transformers.dynamic_module_utils")
        dynamic_module_utils.get_imports = lambda filename: [filename]

        modelscope_pkg = types.ModuleType("modelscope")
        modelscope_utils = types.ModuleType("modelscope.utils")
        modelscope_plugins = types.ModuleType("modelscope.utils.plugins")
        modelscope_utils.plugins = modelscope_plugins
        modelscope_pkg.utils = modelscope_utils

        monkeypatch.setitem(sys.modules, "datasets", datasets_pkg)
        monkeypatch.setitem(sys.modules, "datasets.load", datasets_load)
        monkeypatch.setitem(sys.modules, "datasets.packaged_modules", datasets_packaged_modules)
        monkeypatch.setitem(sys.modules, "datasets.utils", datasets_utils)
        monkeypatch.setitem(sys.modules, "datasets.utils.py_utils", datasets_py_utils)
        monkeypatch.setitem(sys.modules, "transformers", transformers_pkg)
        monkeypatch.setitem(sys.modules, "transformers.dynamic_module_utils", dynamic_module_utils)
        monkeypatch.setitem(sys.modules, "modelscope", modelscope_pkg)
        monkeypatch.setitem(sys.modules, "modelscope.utils", modelscope_utils)
        monkeypatch.setitem(sys.modules, "modelscope.utils.plugins", modelscope_plugins)

        compat.install_compat_shims()

        assert datasets_load.ALL_ALLOWED_EXTENSIONS == [".txt"]
        assert callable(datasets_load.files_to_hash)
        assert datasets_py_utils.get_imports("demo.py") == ["demo.py"]
        assert modelscope_plugins.install_module_from_requirements("requirements.txt") is None
