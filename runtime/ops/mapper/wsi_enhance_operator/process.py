from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np

from datamate.core.base_op import Mapper

MODELS_ROOT = "/models/WSIEnhance"


def _ensure_path() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _resolve_image_path(sample: Dict[str, Any]) -> str:
    for key in ("filePath", "image_path", "source_path", "text"):
        value = sample.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _resolve_export_root(sample: Dict[str, Any], source_path: str) -> str:
    for key in ("export_path", "exportPath", "output_dir"):
        value = sample.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if source_path:
        return os.path.dirname(source_path)
    return ""


def _resolve_slide_name(sample: Dict[str, Any], source_path: str) -> str:
    file_name = sample.get("fileName")
    if isinstance(file_name, str) and file_name.strip():
        stem, _ = os.path.splitext(file_name.strip())
        if stem:
            return stem
    if source_path:
        return os.path.splitext(os.path.basename(source_path))[0]
    return "wsi_sample"


def _resolve_stage_dir(sample: Dict[str, Any], source_path: str, stage_name: str) -> str:
    export_root = _resolve_export_root(sample, source_path)
    slide_name = _resolve_slide_name(sample, source_path)
    return os.path.abspath(os.path.join(export_root, slide_name, stage_name))


def _save_png(path: str, rgb: np.ndarray) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    cv2.imwrite(path, bgr)


def _contours_to_coords(contours: List[np.ndarray]) -> List[List[Tuple[int, int]]]:
    out: List[List[Tuple[int, int]]] = []
    for contour in contours:
        pts = contour.squeeze(axis=1) if getattr(contour, "ndim", 0) == 3 else contour
        out.append([(int(x), int(y)) for x, y in pts])
    return out


def _segmentation_output_to_mask(output: Any, shape: Tuple[int, int]) -> np.ndarray:
    if output is None:
        return np.zeros(shape, dtype=np.uint8)
    mask = np.asarray(output)
    if mask.ndim == 3:
        mask = mask[..., 0]
    return ((mask > 0).astype(np.uint8) * 255)


def _mask_to_patch_coords(
    tissue_mask: np.ndarray,
    wsi_w: int,
    wsi_h: int,
    patch_size: int,
) -> List[Tuple[int, int]]:
    mh, mw = tissue_mask.shape[:2]
    scale_x = wsi_w / mw
    scale_y = wsi_h / mh
    coords: List[Tuple[int, int]] = []
    ys, xs = np.where(tissue_mask > 0)
    if len(xs) == 0:
        return coords
    x_min, x_max = xs.min(), xs.max()
    y_min, y_max = ys.min(), ys.max()
    for y in range(int(y_min * scale_y), int((y_max + 1) * scale_y), patch_size):
        for x in range(int(x_min * scale_x), int((x_max + 1) * scale_x), patch_size):
            cx = int((x + patch_size / 2) / scale_x)
            cy = int((y + patch_size / 2) / scale_y)
            if 0 <= cx < mw and 0 <= cy < mh and tissue_mask[cy, cx] > 0:
                coords.append((x, y))
    return coords


def _keep_patch(patch_rgb: np.ndarray, patch_bg_thresh: int, patch_max_bg_ratio: float) -> bool:
    if patch_rgb is None or patch_rgb.size == 0:
        return False
    gray = cv2.cvtColor(patch_rgb, cv2.COLOR_RGB2GRAY)
    bg_mask = gray > patch_bg_thresh
    return float(bg_mask.mean()) <= patch_max_bg_ratio


def _resolve_device() -> str:
    try:
        import torch

        if hasattr(torch, "npu") and callable(getattr(torch.npu, "is_available", None)) and torch.npu.is_available():
            return "npu:0"
        if torch.cuda.is_available():
            return "cuda:0"
    except Exception:
        pass
    return "cpu"


class WSIEnhanceMapper(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_folder = str(kwargs.get("model_folder", "2025-10-18")).strip() or "2025-10-18"
        self.thumbnail_size = int(kwargs.get("thumbnail_size", 3072))
        self.patch_size = int(kwargs.get("patch_size", 256))
        self.patch_bg_thresh = int(kwargs.get("patch_bg_thresh", 210))
        self.patch_max_bg_ratio = float(kwargs.get("patch_max_bg_ratio", 0.85))

        self.save_patches = _as_bool(kwargs.get("save_patches"), True)

        self.enable_stain_normalize = _as_bool(kwargs.get("enable_stain_normalize"), False)
        self.save_normalized_patches = _as_bool(kwargs.get("save_normalized_patches"), True)
        self.stain_method = str(kwargs.get("stain_method", "macenko")).strip().lower() or "macenko"
        self.stain_target = str(kwargs.get("stain_target", "")).strip()

        self.enable_augmentation = _as_bool(kwargs.get("enable_augmentation"), False)
        self.save_augmented_patches = _as_bool(kwargs.get("save_augmented_patches"), True)
        self.aug_factor = int(kwargs.get("aug_factor", 1))
        self.aug_rotate = _as_bool(kwargs.get("aug_rotate"), True)
        self.aug_flip = _as_bool(kwargs.get("aug_flip"), True)
        self.aug_color_jitter = _as_bool(kwargs.get("aug_color_jitter"), True)

        self._processor = None
        self._segmenter = None
        self._augmenter = None
        self._normalizer = None

    def _init_components(self) -> None:
        if self._processor is not None and self._segmenter is not None:
            return

        _ensure_path()
        from slidesegmenter.slidesegmenter import SlideSegmenter
        from wsi_processor.wsi_processor import ProcessorConfig, WSIProcessor

        model_dir = os.path.join(MODELS_ROOT, self.model_folder)
        if not os.path.exists(model_dir):
            raise FileNotFoundError(f"SlideSegmenter model directory not found: {model_dir}")

        self._processor = WSIProcessor(ProcessorConfig())
        self._segmenter = SlideSegmenter(
            channels_last=True,
            tissue_segmentation=True,
            pen_marking_segmentation=True,
            separate_cross_sections=False,
            device=_resolve_device(),
            model_folder=self.model_folder,
            alternative_directory=MODELS_ROOT,
        )

        if self.enable_stain_normalize and self._normalizer is None:
            from stain_normalization.stain_normalization import (
                StainMethod,
                StainNormalizationConfig,
                StainNormalizer,
            )

            method = {
                "macenko": StainMethod.MACENKO,
                "reinhard": StainMethod.REINHARD,
                "vahadane": StainMethod.VAHADANE,
            }.get(self.stain_method, StainMethod.MACENKO)
            config = StainNormalizationConfig(method=method)
            self._normalizer = StainNormalizer(config)
            if self.stain_target and os.path.exists(self.stain_target):
                target = cv2.imread(self.stain_target)
                if target is not None:
                    target = cv2.cvtColor(target, cv2.COLOR_BGR2RGB)
                    self._normalizer.set_target_image(target)

        if self.enable_augmentation and self._augmenter is None:
            from augmentations.augmentations import AugmentationConfig, Augmenter

            config = AugmentationConfig(
                enable_rotate=self.aug_rotate,
                enable_flip=self.aug_flip,
                enable_color_jitter=self.aug_color_jitter,
            )
            self._augmenter = Augmenter(config)

    def _effective_save_patches(self) -> bool:
        # Once stain normalization is enabled, raw patches become transient inputs
        # and should not be persisted as final dataset artifacts.
        return self.save_patches and not self.enable_stain_normalize

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._init_components()
            from wsi_reader.wsi_reader import WSIReader

            image_path = _resolve_image_path(sample)
            if not image_path or not os.path.exists(image_path):
                sample["wsi_enhance_error"] = f"Input WSI not found: {image_path}"
                return sample

            segmentation_dir = _resolve_stage_dir(sample, image_path, "segmentation")
            extract_dir = _resolve_stage_dir(sample, image_path, "patch_extract")
            os.makedirs(segmentation_dir, exist_ok=True)
            os.makedirs(extract_dir, exist_ok=True)

            patch_dir = os.path.join(extract_dir, "patches")
            normalized_dir = os.path.join(extract_dir, "patches_normalized")
            augmented_dir = os.path.join(extract_dir, "patches_augmented")
            save_raw_patches = self._effective_save_patches()

            if save_raw_patches:
                os.makedirs(patch_dir, exist_ok=True)
            if self.enable_stain_normalize:
                os.makedirs(normalized_dir, exist_ok=True)
            if self.enable_augmentation:
                os.makedirs(augmented_dir, exist_ok=True)

            kept_positions: List[Dict[str, int]] = []
            saved_patch_files: List[str] = []
            normalized_files: List[str] = []
            augmented_files: List[str] = []
            patch_count = 0
            normalized_count = 0
            augmented_count = 0

            with WSIReader(image_path) as reader:
                wsi_w, wsi_h = reader.width, reader.height
                thumbnail = reader.get_thumbnail((self.thumbnail_size, self.thumbnail_size))
                prediction = self._segmenter.segment(thumbnail.astype(np.float32) / 255.0)
                tissue_mask = _segmentation_output_to_mask(prediction.get("tissue"), thumbnail.shape[:2])
                pen_mask = _segmentation_output_to_mask(prediction.get("pen"), thumbnail.shape[:2])
                detection = self._processor.build_detection_from_external_masks(
                    thumbnail_rgb=thumbnail,
                    tissue_mask=tissue_mask,
                    note_mask=pen_mask,
                    global_stain_mask=pen_mask,
                )

                overlay = thumbnail.copy()
                cv2.drawContours(overlay, detection.contours["tissue"], -1, (0, 255, 0), 2)
                cv2.drawContours(overlay, detection.contours["note"], -1, (255, 0, 0), 2)
                if detection.contours.get("artifact"):
                    cv2.drawContours(overlay, detection.contours["artifact"], -1, (0, 165, 255), 2)
                if detection.contours.get("bubble"):
                    cv2.drawContours(overlay, detection.contours["bubble"], -1, (0, 0, 255), 2)

                thumb_path = os.path.join(segmentation_dir, "thumbnail.png")
                overlay_path = os.path.join(segmentation_dir, "thumbnail_overlay.png")
                coords_path = os.path.join(segmentation_dir, "coords_thumbnail.json")

                _save_png(thumb_path, thumbnail)
                _save_png(overlay_path, overlay)

                coords = {
                    "source_path": image_path,
                    "tissue_contours": _contours_to_coords(detection.contours["tissue"]),
                    "note_contours": _contours_to_coords(detection.contours["note"]),
                    "artifact_contours": _contours_to_coords(detection.contours.get("artifact", [])),
                    "bubble_contours": _contours_to_coords(detection.contours.get("bubble", [])),
                }
                with open(coords_path, "w", encoding="utf-8") as fh:
                    json.dump(coords, fh, ensure_ascii=False, indent=2)

                tissue_for_patches = cv2.bitwise_and(detection.tissue_mask, cv2.bitwise_not(detection.note_mask))
                tissue_for_patches = cv2.bitwise_and(tissue_for_patches, cv2.bitwise_not(detection.artifact_mask))
                patch_coords = _mask_to_patch_coords(tissue_for_patches, wsi_w, wsi_h, self.patch_size)

                for x, y in patch_coords:
                    patch = reader.read_region(x, y, self.patch_size, self.patch_size, level=0)
                    if not _keep_patch(patch, self.patch_bg_thresh, self.patch_max_bg_ratio):
                        continue

                    patch_count += 1
                    kept_positions.append({"x": int(x), "y": int(y)})
                    base_name = f"patch_{x}_{y}"
                    patch_name = f"{base_name}.png"

                    if save_raw_patches:
                        patch_path = os.path.join(patch_dir, patch_name)
                        _save_png(patch_path, patch)
                        saved_patch_files.append(patch_path)

                    stain_source = patch
                    if self.enable_stain_normalize and self._normalizer is not None:
                        normalized = self._normalizer.normalize(patch)
                        stain_source = normalized
                        normalized_count += 1
                        if self.save_normalized_patches:
                            normalized_path = os.path.join(normalized_dir, patch_name)
                            _save_png(normalized_path, normalized)
                            normalized_files.append(normalized_path)

                    if self.enable_augmentation and self._augmenter is not None:
                        outputs = self._augmenter.generate_augmented_batch(stain_source, n=self.aug_factor)
                        for idx, aug in enumerate(outputs, start=1):
                            augmented_count += 1
                            if self.save_augmented_patches:
                                augmented_path = os.path.join(augmented_dir, f"{base_name}_aug{idx}.png")
                                _save_png(augmented_path, aug)
                                augmented_files.append(augmented_path)

            patch_positions_path = os.path.join(extract_dir, "patch_positions.json")
            with open(patch_positions_path, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "source_path": image_path,
                        "wsi_size": {"w": int(wsi_w), "h": int(wsi_h)},
                        "patch_size": self.patch_size,
                        "patch_count": patch_count,
                        "patches": kept_positions,
                    },
                    fh,
                    ensure_ascii=False,
                    indent=2,
                )

            stain_manifest_path = ""
            if self.enable_stain_normalize:
                stain_manifest_path = os.path.join(normalized_dir, "stain_normalize_manifest.json")
                with open(stain_manifest_path, "w", encoding="utf-8") as fh:
                    json.dump(
                        {
                            "source_path": image_path,
                            "input_count": patch_count,
                            "normalized_count": normalized_count,
                            "saved_count": len(normalized_files),
                            "save_normalized_patches": self.save_normalized_patches,
                            "normalized_files": normalized_files,
                        },
                        fh,
                        ensure_ascii=False,
                        indent=2,
                    )

            augmentation_manifest_path = ""
            if self.enable_augmentation:
                augmentation_manifest_path = os.path.join(augmented_dir, "augmentation_manifest.json")
                with open(augmentation_manifest_path, "w", encoding="utf-8") as fh:
                    json.dump(
                        {
                            "source_mode": "normalized" if self.enable_stain_normalize else "raw",
                            "input_count": normalized_count if self.enable_stain_normalize else patch_count,
                            "augmented_count": augmented_count,
                            "saved_count": len(augmented_files),
                            "save_augmented_patches": self.save_augmented_patches,
                            "augmented_files": augmented_files,
                        },
                        fh,
                        ensure_ascii=False,
                        indent=2,
                    )

            pipeline_manifest_path = os.path.join(extract_dir, "pipeline_manifest.json")
            with open(pipeline_manifest_path, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "source_path": image_path,
                        "model_root": MODELS_ROOT,
                        "model_folder": self.model_folder,
                        "thumbnail_size": self.thumbnail_size,
                        "patch_size": self.patch_size,
                        "patch_bg_thresh": self.patch_bg_thresh,
                        "patch_max_bg_ratio": self.patch_max_bg_ratio,
                        "save_patches": self.save_patches,
                        "effective_save_patches": save_raw_patches,
                        "enable_stain_normalize": self.enable_stain_normalize,
                        "save_normalized_patches": self.save_normalized_patches,
                        "stain_method": self.stain_method,
                        "stain_target": self.stain_target,
                        "enable_augmentation": self.enable_augmentation,
                        "save_augmented_patches": self.save_augmented_patches,
                        "aug_factor": self.aug_factor,
                        "aug_rotate": self.aug_rotate,
                        "aug_flip": self.aug_flip,
                        "aug_color_jitter": self.aug_color_jitter,
                        "patch_count": patch_count,
                        "normalized_count": normalized_count,
                        "augmented_count": augmented_count,
                        "segmentation_dir": segmentation_dir,
                        "patch_extract_dir": extract_dir,
                    },
                    fh,
                    ensure_ascii=False,
                    indent=2,
                )

            sample["thumbnail_path"] = thumb_path
            sample["thumbnail_overlay_path"] = overlay_path
            sample["coords_thumbnail_json"] = coords_path
            sample["patch_positions_json"] = patch_positions_path
            sample["pipeline_manifest_json"] = pipeline_manifest_path
            sample["patch_count"] = patch_count
            sample["normalized_patch_count"] = normalized_count
            sample["augmented_count"] = augmented_count
            sample["patches_dir"] = patch_dir if save_raw_patches else ""
            sample["normalized_patches_dir"] = normalized_dir if self.enable_stain_normalize and self.save_normalized_patches else ""
            sample["augmented_patches_dir"] = augmented_dir if self.enable_augmentation and self.save_augmented_patches else ""
            if stain_manifest_path:
                sample["stain_normalize_manifest_json"] = stain_manifest_path
            if augmentation_manifest_path:
                sample["augmentation_manifest_json"] = augmentation_manifest_path
            sample["wsi_enhance_metadata"] = {
                "model_root": MODELS_ROOT,
                "model_folder": self.model_folder,
                "thumbnail_size": self.thumbnail_size,
                "patch_size": self.patch_size,
                "patch_bg_thresh": self.patch_bg_thresh,
                "patch_max_bg_ratio": self.patch_max_bg_ratio,
                "save_patches": self.save_patches,
                "effective_save_patches": save_raw_patches,
                "enable_stain_normalize": self.enable_stain_normalize,
                "save_normalized_patches": self.save_normalized_patches,
                "enable_augmentation": self.enable_augmentation,
                "save_augmented_patches": self.save_augmented_patches,
                "output_dir": os.path.dirname(segmentation_dir),
            }
            return sample
        except Exception as exc:
            sample["wsi_enhance_error"] = str(exc)
            return sample
