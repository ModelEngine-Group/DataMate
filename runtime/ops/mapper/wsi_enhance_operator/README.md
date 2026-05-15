# WSIEnhance Operator

## Overview

`wsi_enhance_operator` is a custom mapper operator package for DataMate.

It includes:

- operator registration entry
- operator metadata and UI settings
- main pipeline implementation
- WSI reading helpers
- slide segmentation helpers
- patch extraction helpers
- stain normalization helpers
- augmentation helpers

## Directory Structure

```text
wsi_enhance_operator/
├── __init__.py
├── metadata.yml
├── process.py
├── README.md
├── requirements.txt
├── augmentations/
│   ├── __init__.py
│   └── augmentations.py
├── slidesegmenter/
│   ├── __init__.py
│   ├── _model_utils.py
│   ├── slidesegmenter.py
│   └── model_files/
│       └── __init__.py
├── stain_normalization/
│   ├── __init__.py
│   └── stain_normalization.py
├── wsi_processor/
│   ├── __init__.py
│   └── wsi_processor.py
└── wsi_reader/
    ├── __init__.py
    ├── wsi_reader.py
    └── wsi_types.py
```

## File Responsibilities

- `__init__.py`: registers `WSIEnhanceMapper` into DataMate operator registry
- `metadata.yml`: defines operator identity, category, runtime resources, and frontend settings
- `process.py`: main mapper entry, parameter parsing, segmentation, patch extraction, and artifact export
- `augmentations/`: patch augmentation utilities
- `slidesegmenter/`: segmentation model loading and inference helpers
- `stain_normalization/`: stain normalization logic
- `wsi_processor/`: contour and detection post-processing helpers
- `wsi_reader/`: WSI file reading abstraction
- `requirements.txt`: Python dependencies required by this operator package

## Model Path

The runtime environment is expected to provide model files under:

- `/models/WSIEnhance/<model_folder>`

Default `model_folder`:

- `2025-10-18`

## Input Expectations

The operator accepts a `sample` dictionary. Common supported input fields are:

- `filePath`: source WSI path
- `image_path`: source WSI path alias
- `source_path`: optional source path alias
- `export_path`, `exportPath`, or `output_dir`: output root directory

## Main Settings

Common configurable settings in `metadata.yml` include:

- `model_folder`
- `thumbnail_size`
- `patch_size`
- `patch_bg_thresh`
- `patch_max_bg_ratio`
- `save_patches`
- `enable_stain_normalize`
- `save_normalized_patches`
- `stain_method`
- `stain_target`
- `enable_augmentation`
- `save_augmented_patches`
- `aug_factor`
- `aug_rotate`
- `aug_flip`
- `aug_color_jitter`

## Output Layout

For each input slide, the operator can generate:

- `segmentation/thumbnail.png`
- `segmentation/thumbnail_overlay.png`
- `segmentation/coords_thumbnail.json`
- `patch_extract/patch_positions.json`
- `patch_extract/pipeline_manifest.json`
- `patch_extract/patches/` when raw patch saving is enabled
- `patch_extract/patches_normalized/` when stain normalization output saving is enabled
- `patch_extract/patches_augmented/` when augmentation output saving is enabled

## Output Fields

The operator writes result paths and summary fields back into `sample`. Common output fields include:

- `thumbnail_path`
- `thumbnail_overlay_path`
- `coords_thumbnail_json`
- `patch_positions_json`
- `pipeline_manifest_json`
- `patch_count`
- `normalized_patch_count`
- `augmented_count`
- `patches_dir`
- `normalized_patches_dir`
- `augmented_patches_dir`

## Usage Notes

1. Place the operator directory under `runtime/ops/mapper/wsi_enhance_operator`.
2. Ensure `metadata.yml`, `process.py`, and `__init__.py` are present.
3. Ensure required WSI runtime dependencies are installed, including OpenSlide-related dependencies.
4. Ensure model files are mounted under `/models/WSIEnhance/<model_folder>`.
5. Import the operator package from `runtime/ops/mapper/__init__.py`.
6. Configure parameters from the DataMate frontend or task definition.
