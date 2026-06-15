from __future__ import annotations

import importlib
import sys
import types

import numpy as np
import pytest


def import_normalizer_module(monkeypatch: pytest.MonkeyPatch):
    fake_torch = types.ModuleType("torch")

    class FakeNPU:
        @staticmethod
        def is_available():
            return False

        @staticmethod
        def get_device_name(_index):
            return "fake-npu"

    fake_torch.npu = FakeNPU()
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(sys.modules, "torch_npu", types.ModuleType("torch_npu"))

    fake_faiss = types.ModuleType("faiss")

    class FakeIndexFlatIP:
        def __init__(self, dim):
            self.d = dim
            self.vectors = None

        def add(self, vectors):
            self.vectors = vectors

        def search(self, query_vecs, k):
            scores = np.ones((len(query_vecs), k), dtype="float32")
            indices = np.zeros((len(query_vecs), k), dtype="int64")
            return scores, indices

    def read_index(_path):
        return FakeIndexFlatIP(2)

    def write_index(_index, _path):
        return None

    fake_faiss.IndexFlatIP = FakeIndexFlatIP
    fake_faiss.read_index = read_index
    fake_faiss.write_index = write_index
    monkeypatch.setitem(sys.modules, "faiss", fake_faiss)

    sentence_transformers = types.ModuleType("sentence_transformers")

    class FakeSentenceTransformer:
        def __init__(self, model_dir, device=None):
            self.model_dir = model_dir
            self.device = device

        def encode(self, texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False, batch_size=24):
            del convert_to_numpy, normalize_embeddings, show_progress_bar, batch_size
            if isinstance(texts, str):
                texts = [texts]
            return np.ones((len(texts), 2), dtype="float32")

    sentence_transformers.SentenceTransformer = FakeSentenceTransformer
    monkeypatch.setitem(sys.modules, "sentence_transformers", sentence_transformers)

    sys.modules.pop("normalizer.normalizer_npu", None)
    return importlib.import_module("normalizer.normalizer_npu")


class TestMedicalNormalizer:
    def test_normalize_term_text(self, monkeypatch: pytest.MonkeyPatch):
        normalizer_module = import_normalizer_module(monkeypatch)

        assert normalizer_module.normalize_term_text("  Foo Bar  ") == "foobar"
        assert normalizer_module.normalize_term_text("") == ""

    def test_process_search_results_threshold(self, monkeypatch: pytest.MonkeyPatch):
        normalizer_module = import_normalizer_module(monkeypatch)
        normalizer = normalizer_module.MedicalNormalizer.__new__(normalizer_module.MedicalNormalizer)
        normalizer.std_terms = [{"name": "appendicitis", "code": "A01"}]
        results = [None, None]

        normalizer._process_search_results(
            np.array([[0.91], [0.5]], dtype="float32"),
            np.array([[0], [0]], dtype="int64"),
            [0, 1],
            results,
        )

        assert results[0]["source"] == "Vector_Retrieval"
        assert results[0]["std_code"] == "A01"
        assert results[1]["source"] == "Unmapped_Low_Score"
        assert results[1]["std_name"] is None

    def test_normalize_batch_prefers_curated_then_l1_then_vector(self, monkeypatch: pytest.MonkeyPatch):
        normalizer_module = import_normalizer_module(monkeypatch)
        normalizer = normalizer_module.MedicalNormalizer.__new__(normalizer_module.MedicalNormalizer)
        normalizer.curated_rules = {
            "ruled": {"std_name": "Rule Hit", "std_code": "R1"},
        }
        normalizer.use_l1_cache = True
        normalizer.l1_cache = {
            "cached": {"std_name": "Cache Hit", "code": "C1"},
        }
        normalizer.std_terms = [{"name": "Vector Hit", "code": "V1"}]
        normalizer._get_embeddings = lambda texts: np.ones((len(texts), 2), dtype="float32")
        normalizer._search_batch = lambda vecs, k: (
            np.array([[0.95], [0.4]], dtype="float32"),
            np.array([[0], [0]], dtype="int64"),
        )

        results = normalizer.normalize_batch(["ruled", "cached", "vector", "miss"])

        assert results[0]["source"] == "Curated_Rule"
        assert results[1]["source"] == "L1_Cache"
        assert results[2]["source"] == "Vector_Retrieval"
        assert results[3]["source"] == "Unmapped_Low_Score"
