import importlib.util
import subprocess
from pathlib import Path


def _load_check_module():
    module_path = Path(__file__).resolve().parents[1] / "check_npu_runtime.py"
    spec = importlib.util.spec_from_file_location("check_npu_runtime_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_module_probe_runs_each_import_in_isolated_process(monkeypatch):
    check = _load_check_module()
    commands = []

    def fake_run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout='{"available": true, "version": "x"}\n', stderr="")

    monkeypatch.setattr(check.subprocess, "run", fake_run)

    assert check._module_version("torch_npu") == {"available": True, "version": "x"}
    assert commands[0][0] == check.sys.executable
    assert "importlib.import_module('torch_npu')" in commands[0][2]


def test_main_accepts_split_torch_and_paddle_npu_probe_success(monkeypatch, tmp_path, capsys):
    check = _load_check_module()
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    monkeypatch.setattr(check, "_module_version", lambda name: {"available": True, "version": name})
    monkeypatch.setenv("UNSTRUCTUREDIO_YOLOX_MODEL_PATH", str(model_dir))
    monkeypatch.setenv("UNSTRUCTUREDIO_YOLOX_SRC_PATH", str(model_dir))
    monkeypatch.setenv("UNSTRUCTUREDIO_OCR_DET_MODEL_DIR", str(model_dir))
    monkeypatch.setenv("UNSTRUCTUREDIO_OCR_REC_MODEL_DIR", str(model_dir))
    monkeypatch.setenv("UNSTRUCTUREDIO_OCR_CLS_MODEL_DIR", str(model_dir))

    assert check.main() == 0
    report = capsys.readouterr().out
    assert '"torch_npu"' in report
    assert '"paddleocr"' in report


def test_module_probe_injects_ascend_library_paths(monkeypatch):
    check = _load_check_module()
    seen_envs = []

    def fake_exists(path):
        return path in {"/opt/ascend/lib", "/tmp/existing"}

    def fake_run(command, **kwargs):
        seen_envs.append(kwargs["env"])
        return subprocess.CompletedProcess(command, 0, stdout='{"available": true, "version": "x"}\n', stderr="")

    monkeypatch.setattr(check.os.path, "exists", fake_exists)
    monkeypatch.setattr(check, "ASCEND_NPU_LIBRARY_PATHS", ("/opt/ascend/lib", "/missing"))
    monkeypatch.setenv("LD_LIBRARY_PATH", "/tmp/existing")
    monkeypatch.setattr(check.subprocess, "run", fake_run)

    assert check._module_version("paddle")["available"] is True
    assert seen_envs[0]["LD_LIBRARY_PATH"].split(":") == ["/opt/ascend/lib", "/tmp/existing"]
