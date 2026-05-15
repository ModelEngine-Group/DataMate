# MedCleanStd Full Operator

## Overview

`medcleanstd_full_operator` is a custom mapper operator package for DataMate.

It includes:

- operator registration entry
- operator metadata and UI settings
- main pipeline implementation
- document parsing helper code
- text correction helper code
- NER helper code
- term normalization helper code

## Directory Structure

```text
medcleanstd_full_operator/
├── __init__.py
├── metadata.yml
├── process.py
├── README.md
├── requirements.txt
├── myparser/
│   └── parser.py
├── mycorrector/
│   ├── confusion_dict.json
│   ├── corrector.py
│   └── update_l1cache.py
├── ner/
│   ├── compat.py
│   ├── ner_npu.py
│   └── siamese_uie_pipeline_batch.py
└── normalizer/
    ├── accuracy_term_rules.json
    ├── l1_cache.json
    ├── normalizer_npu.py
    ├── std_terms.index
    └── std_terms.json
```

## File Responsibilities

- `__init__.py`: registers `MedCleanStdFullMapper` into DataMate operator registry
- `metadata.yml`: defines operator identity, category, runtime resources, and frontend settings
- `process.py`: main mapper entry, parameter parsing, stage orchestration, and result export
- `myparser/`: document parsing helpers
- `mycorrector/`: medical text correction helpers and dictionary resources
- `ner/`: SiameseUIE-based NER runtime helpers
- `normalizer/`: medical term normalization logic and resources
- `requirements.txt`: Python dependencies required by this operator package

## Model Paths

The runtime environment is expected to provide:

- `/models/MedCleanStd/SiameseUIE`
- `/models/MedCleanStd/bge-small-zh-v1.5`

## Input Expectations

The operator accepts a `sample` dictionary. Common supported input fields are:

- `filePath` or `file_path`: source document path
- `source_path`: optional source path alias
- `text`: raw text input when no local file is used
- `export_path` or `exportPath`: optional output directory override

## Main Settings

Common configurable settings in `metadata.yml` include:

- `parse_overwrite_text`
- `use_proper_corrector`
- `segment_length`
- `max_text_length`
- `correct_overwrite_text`
- `ner_schema`
- `inference_batch_size`
- `max_sentences`
- `use_l1_cache`
- `batch_size`
- `max_entity_length`

## Output Fields

The operator writes intermediate and final results back into `sample`. Common output fields include:

- `parsed_text`
- `corrected_text`
- `entities`
- `normalized_entities`
- `entity_count`
- `normalized_entity_count`
- `result_json_path`
- `medclean_pipeline_status`

## Usage Notes

1. Place the operator directory under `runtime/ops/mapper/medcleanstd_full_operator`.
2. Ensure `metadata.yml`, `process.py`, and `__init__.py` are present.
3. Ensure required models are mounted under `/models/MedCleanStd`.
4. Import the operator package from `runtime/ops/mapper/__init__.py`.
5. Configure parameters from the DataMate frontend or task definition.

## Result Export

When a valid source path and export directory are available, the operator writes a JSON result file beside the processed output and stores the path in `result_json_path`.
