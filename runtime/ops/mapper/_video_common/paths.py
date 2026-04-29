# -*- coding: utf-8 -*-
import os
import time
import uuid

def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)
    return p

def make_run_dir(export_path: str, op_name: str):
    """
    统一输出目录：{export_path}/{op_name}/{timestamp_uuid}/
    """
    ts = time.strftime("%Y%m%d_%H%M%S")
    run_id = f"{ts}_{uuid.uuid4().hex[:8]}"
    out_dir = os.path.join(export_path, op_name, run_id)
    ensure_dir(out_dir)
    return out_dir