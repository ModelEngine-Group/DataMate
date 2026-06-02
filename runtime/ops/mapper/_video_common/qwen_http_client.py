# -*- coding: utf-8 -*-
import os
import json
import cv2
import requests


DEFAULT_QWEN_VL_ENDPOINT = "http://qwen-vl-service:18080"


def resolve_qwenvl_service_url(service_url: str | None = None) -> str:
    return (service_url or os.getenv("QWEN_VL_ENDPOINT") or DEFAULT_QWEN_VL_ENDPOINT).rstrip("/")


def qwenvl_infer_by_image_path(
    image_path: str,
    task: str,
    service_url: str | None = None,
    max_new_tokens: int = 64,
    language: str = "zh",
    style: str = "normal",
    timeout: int = 180,
):
    """
    对齐你当前服务端 qwen_vl_server.py 的接口：
      POST {service_url}/infer
      JSON: {image_path, task, max_new_tokens, language, style}

    返回：服务端 jsonify 的 dict
    """
    sess = requests.Session()
    sess.trust_env = False  # 避免系统代理拦 localhost

    payload = {
        "image_path": image_path,
        "task": task,
        "max_new_tokens": int(max_new_tokens),
        "language": language,
        "style": style,
    }
    service_url = resolve_qwenvl_service_url(service_url)
    r = sess.post(service_url + "/infer", json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if data.get("error"):
        reason = str(data.get("reason", data["error"]))
        raise RuntimeError(f"QwenVL infer failed for task={task}: {reason}")
    return data


def qwenvl_correct_subtitle_srt(
    srt_text: str,
    service_url: str | None = None,
    language: str = "auto",
    max_new_tokens: int = 1024,
    timeout: int = 180,
):
    sess = requests.Session()
    sess.trust_env = False

    payload = {
        "task": "subtitle_correct",
        "srt_text": str(srt_text or ""),
        "language": language,
        "max_new_tokens": int(max_new_tokens),
    }
    service_url = resolve_qwenvl_service_url(service_url)
    r = sess.post(service_url + "/text", json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if data.get("error"):
        reason = str(data.get("reason", data["error"]))
        raise RuntimeError(f"QwenVL subtitle correction failed: {reason}")
    return data

def save_frame_to_jpg(frame_bgr, out_path: str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    ok = cv2.imwrite(out_path, frame_bgr)
    if not ok:
        raise RuntimeError(f"failed to write jpg: {out_path}")
    return out_path
