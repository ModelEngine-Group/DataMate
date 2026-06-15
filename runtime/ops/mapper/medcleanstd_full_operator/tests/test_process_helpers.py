from __future__ import annotations

import json
from pathlib import Path

import pytest

import process


class TestProcessHelpers:
    def test_resolve_input_and_text_priority(self):
        sample = {
            "text": "raw",
            "parsed_text": "parsed",
            "corrected_text": "corrected",
            "source_path": "from-source.txt",
            "filePath": " from-file.txt ",
        }

        assert process._resolve_input(sample) == "from-file.txt"
        assert process._resolve_text(sample) == "corrected"
        assert process._resolve_source_path(sample) == "from-file.txt"

    def test_resolve_export_dir_and_result_json_path(self, tmp_path: Path):
        source_path = tmp_path / "inputs" / "case_record_1.txt"
        source_path.parent.mkdir(parents=True)
        source_path.write_text("content", encoding="utf-8")

        export_dir = tmp_path / "outputs"
        sample = {
            "filePath": str(source_path),
            "export_path": str(export_dir),
            "fileName": "custom_name.txt",
        }

        assert process._resolve_export_dir(sample, str(source_path)) == str(export_dir)
        assert process._resolve_result_json_path(sample) == str(export_dir / "custom_name.json")

    def test_persist_result_json_writes_payload(self, tmp_path: Path):
        source_path = tmp_path / "inputs" / "case_record_2.txt"
        source_path.parent.mkdir(parents=True)
        source_path.write_text("content", encoding="utf-8")

        sample = {
            "filePath": str(source_path),
            "export_path": str(tmp_path / "dataset"),
            "value": 123,
        }

        result_path = process._persist_result_json(sample)
        payload = json.loads(Path(result_path).read_text(encoding="utf-8"))

        assert Path(result_path).exists()
        assert payload["value"] == 123
        assert payload["result_json_path"] == result_path

    @pytest.mark.unit
    def test_split_by_sentences_groups_by_limit(self):
        text = "A. B. C.\nD"
        parts = process._split_by_sentences(text, max_sentences=2)

        assert parts == ["A. B.", " C.D"]

    def test_mapper_init_uses_schema_aliases_and_flags(self):
        mapper = process.MedCleanStdFullMapper(
            ner_schema="disease,exam,custom",
            use_l1_cache="false",
            batch_size="8",
            max_sentences="3",
        )

        assert mapper.ner_schema == [
            process.SCHEMA_ALIASES["disease"],
            process.SCHEMA_ALIASES["exam"],
            "custom",
        ]
        assert mapper.use_l1_cache is False
        assert mapper.batch_size == 8
        assert mapper.max_sentences == 3

    def test_run_normalize_without_entities_still_persists_json(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        mapper = process.MedCleanStdFullMapper()
        monkeypatch.setattr(mapper, "_init_normalizer", lambda: None)

        source_path = tmp_path / "case_record_3.txt"
        source_path.write_text("text", encoding="utf-8")
        sample = {
            "filePath": str(source_path),
            "export_path": str(tmp_path / "result"),
            "entities": [],
        }

        mapper._run_normalize(sample)

        assert sample["normalized_entities"] == []
        assert sample["normalized_entity_count"] == 0
        assert sample["dropped_entities_count"] == 0
        assert sample["medclean_normalize_metadata"]["skipped_reason"] == "no_entities"
        assert Path(sample["result_json_path"]).exists()
