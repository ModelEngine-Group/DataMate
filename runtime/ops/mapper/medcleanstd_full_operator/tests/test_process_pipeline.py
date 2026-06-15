from __future__ import annotations

from pathlib import Path

import pytest

import process


class FakeParser:
    def __init__(self):
        self.seen = []

    def parse(self, source):
        self.seen.append(source)
        return "parsed-content"


class FakeCorrector:
    def correct(self, text):
        return f"{text}-corrected", {"errors": [], "source": text, "target": f"{text}-corrected"}


class FakeNER:
    def extract(self, text, schema):
        return [{"text": text.strip(), "label": schema[0], "start": 1, "end": 3}]


class FakeNormalizer:
    def normalize_batch(self, texts):
        return [
            {"std_name": f"std-{text}", "std_code": f"code-{idx}", "score": 1.0, "source": "stub"}
            for idx, text in enumerate(texts)
        ]


class TestProcessPipeline:
    def test_run_parse_uses_parser_for_existing_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        mapper = process.MedCleanStdFullMapper()
        fake_parser = FakeParser()
        mapper._parser = fake_parser
        monkeypatch.setattr(mapper, "_init_parser", lambda: None)

        source_path = tmp_path / "case_record_1.txt"
        source_path.write_text("raw", encoding="utf-8")
        sample = {"filePath": str(source_path)}

        mapper._run_parse(sample)

        assert sample["parsed_text"] == "parsed-content"
        assert sample["text"] == "parsed-content"
        assert sample["parsed_source_path"] == str(source_path)
        assert fake_parser.seen == [str(source_path)]

    def test_run_correct_overwrites_text(self, monkeypatch: pytest.MonkeyPatch):
        mapper = process.MedCleanStdFullMapper(correct_overwrite_text="true")
        mapper._corrector = FakeCorrector()
        monkeypatch.setattr(mapper, "_init_corrector", lambda: None)
        sample = {"text": "before"}

        mapper._run_correct(sample)

        assert sample["corrected_text"] == "before-corrected"
        assert sample["text"] == "before-corrected"
        assert sample["medclean_correct_metadata"]["overwrite_text"] is True

    def test_run_ner_adds_chunk_offsets(self, monkeypatch: pytest.MonkeyPatch):
        mapper = process.MedCleanStdFullMapper(max_sentences="2", ner_schema="disease")
        mapper._ner = FakeNER()
        monkeypatch.setattr(mapper, "_init_ner", lambda: None)

        sample = {"text": "A. B. C."}
        mapper._run_ner(sample)

        assert sample["entity_count"] == 2
        assert sample["entities"][0]["chunk_id"] == 0
        assert sample["entities"][0]["global_start"] == 1
        assert sample["entities"][1]["chunk_id"] == 1
        assert sample["entities"][1]["chunk_offset"] == len("A. B.")

    def test_run_normalize_filters_long_entities(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        mapper = process.MedCleanStdFullMapper(max_entity_length="5")
        mapper._normalizer = FakeNormalizer()
        monkeypatch.setattr(mapper, "_init_normalizer", lambda: None)

        source_path = tmp_path / "case_record_4.txt"
        source_path.write_text("raw", encoding="utf-8")
        sample = {
            "filePath": str(source_path),
            "export_path": str(tmp_path / "dataset"),
            "entities": [
                {"text": "short"},
                {"text": "toolong"},
            ],
        }

        mapper._run_normalize(sample)

        assert sample["normalized_entity_count"] == 1
        assert sample["dropped_entities_count"] == 1
        assert sample["entities"][0]["normalized"]["std_name"] == "std-short"
        assert Path(sample["result_json_path"]).exists()

    def test_execute_stops_on_parse_error(self, monkeypatch: pytest.MonkeyPatch):
        mapper = process.MedCleanStdFullMapper()

        def boom(sample):
            raise ValueError("parse failed")

        monkeypatch.setattr(mapper, "_run_parse", boom)
        result = mapper.execute({})

        assert result["medclean_parse_error"] == "parse failed"
        assert result["medclean_pipeline_status"] == {"parse": "error"}

    def test_execute_success_sets_all_stage_status(self, monkeypatch: pytest.MonkeyPatch):
        mapper = process.MedCleanStdFullMapper()

        def run_parse(sample):
            sample["parsed_text"] = "p"

        def run_correct(sample):
            sample["corrected_text"] = "c"

        def run_ner(sample):
            sample["entities"] = []

        def run_normalize(sample):
            sample["normalized_entities"] = []

        monkeypatch.setattr(mapper, "_run_parse", run_parse)
        monkeypatch.setattr(mapper, "_run_correct", run_correct)
        monkeypatch.setattr(mapper, "_run_ner", run_ner)
        monkeypatch.setattr(mapper, "_run_normalize", run_normalize)

        result = mapper.execute({})

        assert result["medclean_pipeline_status"] == {
            "parse": "ok",
            "correct": "ok",
            "ner": "ok",
            "normalize": "ok",
        }
