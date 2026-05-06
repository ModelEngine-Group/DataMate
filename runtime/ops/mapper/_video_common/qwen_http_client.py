# -*- coding: utf-8 -*-
import os
import json
import cv2
import requests

def qwenvl_infer_by_image_path(
    image_path: str,
    task: str,
    service_url: str = "http://127.0.0.1:18080",
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
    r = sess.post(service_url.rstrip("/") + "/infer", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()

def save_frame_to_jpg(frame_bgr, out_path: str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    ok = cv2.imwrite(out_path, frame_bgr)
    if not ok:
        raise RuntimeError(f"failed to write jpg: {out_path}")
    return out_path