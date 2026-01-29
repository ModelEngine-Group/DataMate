# -*- coding: utf-8 -*-
"""结婚证图像合成到实拍背景，从 MarriageCertificate/pics_data_proceed 抽取。无手动选点，仅自动检测+缓存。"""
import json
import os
from typing import Optional, List, Tuple

import cv2
import numpy as np


def cv_imread(file_path: str) -> Optional[np.ndarray]:
    return cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)


def _cv_imwrite(file_path: str, img: np.ndarray) -> bool:
    is_success, im_buf = cv2.imencode(".jpg", img)
    if is_success:
        im_buf.tofile(file_path)
        return True
    return False


def order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def load_cached_coordinates(cache_path: str, image_path: str) -> Optional[np.ndarray]:
    if not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        key = str(image_path).replace("\\", "/")
        if key in data:
            return np.array(data[key], dtype="float32")
    except Exception:
        pass
    return None


def save_cached_coordinates(cache_path: str, image_path: str, coords: np.ndarray) -> None:
    data = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
    key = str(image_path).replace("\\", "/")
    data[key] = coords.tolist()
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def detect_document_corners(image_path: str, cache_path: Optional[str] = None) -> Optional[np.ndarray]:
    """自动检测文档区域，无手动模式。若提供 cache_path 则优先读缓存、检测成功后写缓存。"""
    if cache_path:
        cached = load_cached_coordinates(cache_path, image_path)
        if cached is not None:
            return order_points(cached)
    img = cv_imread(image_path)
    if img is None:
        return None
    ratio = img.shape[0] / 800.0
    processed = cv2.resize(img, (int(img.shape[1] / ratio), 800))
    gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 75, 75)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    v = np.median(gray)
    sigma = 0.33
    lower_thresh = int(max(0, (1.0 - sigma) * v))
    upper_thresh = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(gray, lower_thresh, upper_thresh)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edged = cv2.dilate(edged, kernel, iterations=1)
    cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
    screen_cnt = None
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if 4 <= len(approx) <= 6 and cv2.contourArea(c) > 50000:
            rect = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            screen_cnt = np.int64(box)
            break
    if screen_cnt is None:
        return None
    detected_pts = (screen_cnt * ratio).astype(np.float32)
    ordered = order_points(detected_pts)
    if cache_path:
        save_cached_coordinates(cache_path, image_path, ordered)
    return ordered


def _auto_rotate_to_match_orientation(src: np.ndarray, dst_corners: np.ndarray) -> np.ndarray:
    (tl, tr, br, bl) = dst_corners
    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    dst_w = max(int(width_a), int(width_b))
    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    dst_h = max(int(height_a), int(height_b))
    h_src, w_src = src.shape[:2]
    if (w_src > h_src) != (dst_w > dst_h):
        src = cv2.rotate(src, cv2.ROTATE_90_CLOCKWISE)
    return src


def _pad_src_to_match_ratio(src: np.ndarray, dst_corners: np.ndarray) -> np.ndarray:
    (tl, tr, br, bl) = dst_corners
    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_width = max(int(width_a), int(width_b))
    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_height = max(int(height_a), int(height_b))
    dst_ratio = max_width / float(max_height)
    h_src, w_src = src.shape[:2]
    src_ratio = w_src / float(h_src)
    if abs(src_ratio - dst_ratio) < 0.1:
        return src
    if src_ratio > dst_ratio:
        new_h = int(w_src / dst_ratio)
        total_pad = new_h - h_src
        pad_top = total_pad // 2
        pad_bot = total_pad - pad_top
        return cv2.copyMakeBorder(src, pad_top, pad_bot, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    else:
        new_w = int(h_src * dst_ratio)
        total_pad = new_w - w_src
        pad_left = total_pad // 2
        pad_right = total_pad - pad_left
        return cv2.copyMakeBorder(src, 0, 0, pad_left, pad_right, cv2.BORDER_CONSTANT, value=(255, 255, 255))


def _base_synthesis_pipeline(
    src_path: str,
    dst_path: str,
    dst_corners: np.ndarray,
    output_path: str,
    mode: str = "normal",
    enable_ratio_fix: bool = False,
    enable_auto_rotate: bool = False,
) -> bool:
    src = cv_imread(src_path)
    dst = cv_imread(dst_path)
    if src is None or dst is None:
        return False
    if enable_auto_rotate:
        src = _auto_rotate_to_match_orientation(src, dst_corners)
    if enable_ratio_fix:
        src = _pad_src_to_match_ratio(src, dst_corners)
    h_src, w_src = src.shape[:2]
    src_pts = np.array([[0, 0], [w_src - 1, 0], [w_src - 1, h_src - 1], [0, h_src - 1]], dtype="float32")
    dst_pts = np.array(dst_corners, dtype="float32")
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped_src = cv2.warpPerspective(src, M, (dst.shape[1], dst.shape[0]))
    mask = np.zeros(dst.shape[:2], dtype=np.uint8)
    cv2.fillConvexPoly(mask, dst_pts.astype(int), 255)
    dst_lab = cv2.cvtColor(dst, cv2.COLOR_BGR2LAB)
    warped_lab = cv2.cvtColor(warped_src, cv2.COLOR_BGR2LAB)
    dst_region_l = dst_lab[:, :, 0][mask > 0]
    if dst_region_l.size == 0:
        return False
    l_mean_dst, l_std_dst = np.mean(dst_region_l), np.std(dst_region_l)
    src_region_l = warped_lab[:, :, 0][mask > 0]
    l_mean_src, l_std_src = np.mean(src_region_l), np.std(src_region_l)
    contrast_factor = 0.85 if mode == "shadow" else (0.95 if mode == "tilted" else 1.0)
    l_channel = warped_lab[:, :, 0].astype(float)
    l_channel = (l_channel - l_mean_src) * (l_std_dst / (l_std_src + 1e-5)) * contrast_factor + l_mean_dst
    warped_lab[:, :, 0] = np.clip(l_channel, 0, 255).astype(np.uint8)
    matched_src = cv2.cvtColor(warped_lab, cv2.COLOR_LAB2BGR)
    center = (int((dst_pts[:, 0].min() + dst_pts[:, 0].max()) / 2),
              int((dst_pts[:, 1].min() + dst_pts[:, 1].max()) / 2))
    try:
        final_output = cv2.seamlessClone(matched_src, dst, mask, center, cv2.NORMAL_CLONE)
    except Exception:
        final_output = dst.copy()
        final_output[mask > 0] = matched_src[mask > 0]
    return _cv_imwrite(output_path, final_output)


def run_synthesis(
    src_path: str,
    dst_path: str,
    dst_corners: np.ndarray,
    output_path: str,
    mode: str = "normal",
) -> bool:
    """根据场景 mode 调用合成流水线。"""
    enable_ratio = mode in ("normal", "tilted", "watermark", "incomplete")
    enable_rotate = mode in ("tilted", "watermark", "incomplete")
    return _base_synthesis_pipeline(
        src_path, dst_path, dst_corners, output_path,
        mode=mode,
        enable_ratio_fix=enable_ratio,
        enable_auto_rotate=enable_rotate,
    )
