from __future__ import annotations

import importlib
import sys
import types

import pytest


def import_corrector_module(monkeypatch: pytest.MonkeyPatch):
    pycorrector_module = types.ModuleType("pycorrector")

    class DummyProperCorrector:
        def __init__(self):
            self.calls = []

        def correct(self, text):
            self.calls.append(text)
            return {
                "target": text.upper(),
                "errors": [("src", "dst")],
            }

    pycorrector_module.ProperCorrector = DummyProperCorrector
    monkeypatch.setitem(sys.modules, "pycorrector", pycorrector_module)
    sys.modules.pop("mycorrector.corrector", None)
    return importlib.import_module("mycorrector.corrector")


class TestMedicalCorrector:
    def test_confusion_dict_applied_without_proper(self, monkeypatch: pytest.MonkeyPatch):
        corrector_module = import_corrector_module(monkeypatch)
        corrector = corrector_module.MedicalCorrector(use_proper_corrector=False)
        corrector.confusion_dict = {"abc": "xyz"}
        corrector.sorted_keys = ["abc"]

        result, details = corrector.correct("abc test")

        assert result == "xyz test"
        assert details["confusion_errors"] == [("abc", "xyz")]
        assert details["proper_errors"] == []

    def test_short_text_uses_proper_corrector(self, monkeypatch: pytest.MonkeyPatch):
        corrector_module = import_corrector_module(monkeypatch)
        corrector = corrector_module.MedicalCorrector(
            use_proper_corrector=True,
            segment_length=20,
            max_text_length=100,
        )
        corrector.confusion_dict = {}
        corrector.sorted_keys = []

        result, details = corrector.correct("short")

        assert result == "SHORT"
        assert details["proper_errors"] == [("src", "dst")]
        assert corrector.proper_corrector.calls == ["short"]

    def test_long_text_skips_proper_corrector(self, monkeypatch: pytest.MonkeyPatch):
        corrector_module = import_corrector_module(monkeypatch)
        corrector = corrector_module.MedicalCorrector(
            use_proper_corrector=True,
            segment_length=10,
            max_text_length=5,
        )
        corrector.confusion_dict = {}
        corrector.sorted_keys = []

        result, details = corrector.correct("longer-than-limit")

        assert result == "longer-than-limit"
        assert details["proper_errors"] == []
        assert corrector.proper_corrector.calls == []

    def test_segmentation_path_uses_proper_corrector_per_chunk(self, monkeypatch: pytest.MonkeyPatch):
        corrector_module = import_corrector_module(monkeypatch)
        corrector = corrector_module.MedicalCorrector(
            use_proper_corrector=True,
            segment_length=3,
            max_text_length=100,
        )
        corrector.confusion_dict = {}
        corrector.sorted_keys = []

        result, details = corrector.correct("abcdef")

        assert result == "ABCDEF"
        assert len(corrector.proper_corrector.calls) == 2
        assert details["proper_errors"] == [("src", "dst"), ("src", "dst")]
