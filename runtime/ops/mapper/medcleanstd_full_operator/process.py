from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

from datamate.core.base_op import Mapper

NER_MODEL_DIR = "/models/MedCleanStd/SiameseUIE"
NORMALIZER_MODEL_DIR = "/models/MedCleanStd/bge-small-zh-v1.5"
SCHEMA_ALIASES = {
    "disease": "疾病",
    "symptom": "症状",
    "drug": "药品",
    "surgery": "手术",
    "examination": "检查",
    "exam": "检查",
    "test": "检验",
}


def _ensure_path() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)


def _resolve_input(sample: Dict[str, Any]) -> str:
    for key in ("filePath", "file_path", "source_path", "text"):
        value = sample.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _resolve_text(sample: Dict[str, Any]) -> str:
    for key in ("corrected_text", "parsed_text", "text"):
        value = sample.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _resolve_source_path(sample: Dict[str, Any]) -> str:
    for key in ("filePath", "file_path", "parsed_source_path", "source_path"):
        value = sample.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _resolve_export_dir(sample: Dict[str, Any], source_path: str) -> str:
    for key in ("export_path", "exportPath"):
        value = sample.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    if source_path:
        return os.path.dirname(source_path)
    return ""


def _resolve_result_json_path(sample: Dict[str, Any]) -> str:
    source_path = _resolve_source_path(sample)
    if not source_path:
        return ""

    export_dir = _resolve_export_dir(sample, source_path)
    if not export_dir:
        return ""

    file_name = sample.get("fileName")
    if not isinstance(file_name, str) or not file_name.strip():
        file_name = os.path.basename(source_path)

    stem, _ = os.path.splitext(file_name)
    if not stem:
        stem = "medclean_result"
    return os.path.join(export_dir, f"{stem}.json")


def _persist_result_json(sample: Dict[str, Any]) -> str:
    result_path = _resolve_result_json_path(sample)
    if not result_path:
        raise ValueError("No filePath available for JSON output")

    payload = dict(sample)
    payload["result_json_path"] = result_path
    Path(result_path).parent.mkdir(parents=True, exist_ok=True)
    with open(result_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, default=str)
    return result_path


def _split_by_sentences(text: str, max_sentences: int) -> List[str]:
    if not text:
        return []

    sentences = re.split(r"([。！？；;.!?\n])", text)
    complete_sentences: List[str] = []
    for idx in range(0, len(sentences) - 1, 2):
        sentence = sentences[idx]
        if idx + 1 < len(sentences):
            sentence += sentences[idx + 1]
        if sentence.strip():
            complete_sentences.append(sentence)

    if len(sentences) % 2 == 1 and sentences[-1].strip():
        complete_sentences.append(sentences[-1])

    if not complete_sentences:
        return [text] if text.strip() else []

    groups: List[str] = []
    current: List[str] = []
    count = 0
    for sentence in complete_sentences:
        current.append(sentence)
        count += 1
        if count >= max_sentences:
            groups.append("".join(current))
            current = []
            count = 0
    if current:
        groups.append("".join(current))
    return groups


class MedCleanStdFullMapper(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parse_overwrite_text = str(kwargs.get("parse_overwrite_text", "true")).lower() == "true"
        self.use_proper_corrector = str(kwargs.get("use_proper_corrector", "false")).lower() == "true"
        self.segment_length = int(kwargs.get("segment_length", 100))
        self.max_text_length = int(kwargs.get("max_text_length", 200))
        self.correct_overwrite_text = str(kwargs.get("correct_overwrite_text", "true")).lower() == "true"

        raw_schema = kwargs.get("ner_schema", "疾病,症状")
        if isinstance(raw_schema, str):
            normalized = raw_schema.replace("，", ",")
            schema_items = [item.strip() for item in normalized.split(",") if item.strip()]
        else:
            schema_items = raw_schema or ["疾病", "症状"]
        self.ner_schema = [SCHEMA_ALIASES.get(str(item).strip().lower(), str(item).strip()) for item in schema_items]

        self.inference_batch_size = int(kwargs.get("inference_batch_size", 64))
        self.max_sentences = int(kwargs.get("max_sentences", 80))
        self.use_l1_cache = str(kwargs.get("use_l1_cache", "true")).lower() == "true"
        self.batch_size = int(kwargs.get("batch_size", 24))
        self.max_entity_length = int(kwargs.get("max_entity_length", 50))

        self._parser = None
        self._corrector = None
        self._ner = None
        self._normalizer = None

    def _init_parser(self) -> None:
        if self._parser is not None:
            return
        _ensure_path()
        from myparser.parser import DocParser

        self._parser = DocParser()

    def _init_corrector(self) -> None:
        if self._corrector is not None:
            return
        _ensure_path()
        from mycorrector.corrector import MedicalCorrector

        self._corrector = MedicalCorrector(
            use_proper_corrector=self.use_proper_corrector,
            segment_length=self.segment_length,
            max_text_length=self.max_text_length,
        )

    def _init_ner(self) -> None:
        if self._ner is not None:
            return
        _ensure_path()
        from ner.ner_npu import SiameseNER

        if not os.path.exists(NER_MODEL_DIR):
            raise FileNotFoundError(f"NER model directory not found: {NER_MODEL_DIR}")
        self._ner = SiameseNER(
            model_dir=NER_MODEL_DIR,
            inference_batch_size=self.inference_batch_size,
        )

    def _init_normalizer(self) -> None:
        if self._normalizer is not None:
            return
        _ensure_path()
        from normalizer.normalizer_npu import MedicalNormalizer

        if not os.path.exists(NORMALIZER_MODEL_DIR):
            raise FileNotFoundError(
                f"Normalizer model directory not found: {NORMALIZER_MODEL_DIR}"
            )
        self._normalizer = MedicalNormalizer(
            model_dir=NORMALIZER_MODEL_DIR,
            batch_size=self.batch_size,
            use_l1_cache=self.use_l1_cache,
        )

    def _run_parse(self, sample: Dict[str, Any]) -> None:
        self._init_parser()
        source = _resolve_input(sample)
        if not source:
            raise ValueError("No input source found")

        if os.path.exists(source):
            parsed_text = self._parser.parse(source)
            sample["parsed_source_path"] = source
        else:
            parsed_text = source

        sample["parsed_text"] = parsed_text
        if self.parse_overwrite_text:
            sample["text"] = parsed_text
        sample["medclean_parse_metadata"] = {
            "source_exists": os.path.exists(source),
            "overwrite_text": self.parse_overwrite_text,
        }

    def _run_correct(self, sample: Dict[str, Any]) -> None:
        self._init_corrector()
        input_text = _resolve_text(sample)
        if not input_text:
            raise ValueError("No text found for correction")

        corrected_text, details = self._corrector.correct(input_text)
        sample["corrected_text"] = corrected_text
        sample["correction_details"] = details
        if self.correct_overwrite_text:
            sample["text"] = corrected_text
        sample["medclean_correct_metadata"] = {
            "use_proper_corrector": self.use_proper_corrector,
            "segment_length": self.segment_length,
            "max_text_length": self.max_text_length,
            "overwrite_text": self.correct_overwrite_text,
        }

    def _run_ner(self, sample: Dict[str, Any]) -> None:
        self._init_ner()
        text = _resolve_text(sample)
        if not text:
            raise ValueError("No text found for NER")

        chunks = _split_by_sentences(text, self.max_sentences)
        offsets: List[int] = []
        total = 0
        for chunk in chunks:
            offsets.append(total)
            total += len(chunk)

        entities: List[Dict[str, Any]] = []
        for chunk_id, chunk in enumerate(chunks):
            chunk_entities = self._ner.extract(chunk, schema=self.ner_schema)
            for entity in chunk_entities:
                entity["chunk_id"] = chunk_id
                entity["chunk_offset"] = offsets[chunk_id]
                entity["global_start"] = offsets[chunk_id] + entity.get("start", 0)
                entity["global_end"] = offsets[chunk_id] + entity.get("end", 0)
                entities.append(entity)

        sample["entities"] = entities
        sample["entity_count"] = len(entities)
        sample["medclean_ner_metadata"] = {
            "ner_schema": self.ner_schema,
            "inference_batch_size": self.inference_batch_size,
            "max_sentences": self.max_sentences,
            "model_dir": NER_MODEL_DIR,
        }

    def _run_normalize(self, sample: Dict[str, Any]) -> None:
        self._init_normalizer()
        entities = sample.get("entities") or []
        if not isinstance(entities, list):
            raise ValueError("Invalid entities payload for normalization")

        if not entities:
            sample["normalized_entities"] = []
            sample["normalized_entity_count"] = 0
            sample["dropped_entities_count"] = 0
            sample["entities"] = []
            sample["medclean_normalize_metadata"] = {
                "use_l1_cache": self.use_l1_cache,
                "batch_size": self.batch_size,
                "max_entity_length": self.max_entity_length,
                "model_dir": NORMALIZER_MODEL_DIR,
                "skipped_reason": "no_entities",
            }
            try:
                sample["result_json_path"] = _persist_result_json(sample)
            except Exception as exc:
                sample["result_json_error"] = str(exc)
            return

        texts: List[str] = [str(entity.get("text", "")) for entity in entities]
        normalized_results = self._normalizer.normalize_batch(texts)

        normalized_entities: List[Dict[str, Any]] = []
        dropped_count = 0
        for entity, normalized in zip(entities, normalized_results):
            merged = dict(entity)
            merged["normalized"] = normalized
            length = len(str(merged.get("text", "")))
            if length <= self.max_entity_length:
                normalized_entities.append(merged)
            else:
                dropped_count += 1

        sample["normalized_entities"] = normalized_entities
        sample["normalized_entity_count"] = len(normalized_entities)
        sample["dropped_entities_count"] = dropped_count
        sample["entities"] = normalized_entities
        sample["medclean_normalize_metadata"] = {
            "use_l1_cache": self.use_l1_cache,
            "batch_size": self.batch_size,
            "max_entity_length": self.max_entity_length,
            "model_dir": NORMALIZER_MODEL_DIR,
        }

        try:
            sample["result_json_path"] = _persist_result_json(sample)
        except Exception as exc:
            sample["result_json_error"] = str(exc)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        stage_status: Dict[str, str] = {}
        sample["medclean_pipeline"] = "parse->correct->ner->normalize"

        try:
            self._run_parse(sample)
            stage_status["parse"] = "ok"
        except Exception as exc:
            sample["medclean_parse_error"] = str(exc)
            stage_status["parse"] = "error"
            sample["medclean_pipeline_status"] = stage_status
            return sample

        try:
            self._run_correct(sample)
            stage_status["correct"] = "ok"
        except Exception as exc:
            sample["medclean_correct_error"] = str(exc)
            stage_status["correct"] = "error"
            sample["medclean_pipeline_status"] = stage_status
            return sample

        try:
            self._run_ner(sample)
            stage_status["ner"] = "ok"
        except Exception as exc:
            sample["medclean_ner_error"] = str(exc)
            stage_status["ner"] = "error"
            sample["medclean_pipeline_status"] = stage_status
            return sample

        try:
            self._run_normalize(sample)
            stage_status["normalize"] = "ok"
        except Exception as exc:
            sample["medclean_normalize_error"] = str(exc)
            stage_status["normalize"] = "error"
            sample["medclean_pipeline_status"] = stage_status
            return sample

        sample["medclean_pipeline_status"] = stage_status
        if sample.get("result_json_path"):
            try:
                sample["result_json_path"] = _persist_result_json(sample)
            except Exception as exc:
                sample["result_json_error"] = str(exc)
        return sample
