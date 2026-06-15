from test_pdf_npu_ocr_priority import _load_process_module


def test_process_ascend_env_includes_nnal_and_cann_variants(monkeypatch):
    process = _load_process_module()
    existing = "/tmp/existing_ld"
    accepted = {
        "/usr/local/Ascend/nnal/asdsip/8.5.1/lib",
        "/usr/local/Ascend/nnal/atb/8.5.1/atb/cxx_abi_0/lib",
        "/usr/local/Ascend/nnal/atb/latest/atb/cxx_abi_1/lib",
        "/usr/local/Ascend/cann-8.5.0/lib64",
        existing,
    }

    monkeypatch.setenv("LD_LIBRARY_PATH", existing)
    monkeypatch.setattr(process.os.path, "exists", lambda path: path in accepted)

    process._configure_ascend_runtime_environment()

    paths = process.os.environ["LD_LIBRARY_PATH"].split(":")
    assert paths[:4] == [
        "/usr/local/Ascend/nnal/asdsip/8.5.1/lib",
        "/usr/local/Ascend/nnal/atb/8.5.1/atb/cxx_abi_0/lib",
        "/usr/local/Ascend/nnal/atb/latest/atb/cxx_abi_1/lib",
        "/usr/local/Ascend/cann-8.5.0/lib64",
    ]
    assert paths[-1] == existing
