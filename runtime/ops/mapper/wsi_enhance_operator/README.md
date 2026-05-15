# WSIEnhance Operator

## Overview

This integrated operator runs WSI contour segmentation, patch extraction, optional stain normalization, and optional data augmentation in one pipeline.

## Pipeline Order

- Read the input WSI and generate segmentation artifacts.
- Extract patch coordinates and optionally save raw patches.
- Optionally apply stain normalization to each extracted patch.
- Optionally apply augmentation on normalized patches when stain normalization is enabled, otherwise on raw patches.

## Notes

- When stain normalization is enabled, raw patch files are treated as transient inputs and are not saved even if `save_patches=true`.

## Output Layout

- `segmentation/thumbnail.png`
- `segmentation/thumbnail_overlay.png`
- `segmentation/coords_thumbnail.json`
- `patch_extract/patch_positions.json`
- `patch_extract/patches/` when `save_patches=true`
- `patch_extract/patches_normalized/` when stain normalization is enabled
- `patch_extract/patches_augmented/` when augmentation is enabled
- `patch_extract/pipeline_manifest.json`

## Model Path

- SlideSegmenter model root: `/models/WSIEnhance/<model_folder>`
