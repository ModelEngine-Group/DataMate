# -*- coding: utf-8 -*-
"""结婚证 QA 对生成逻辑，从 MarriageCertificate/form_qa 抽取。"""
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional


def _sanitize(s: str) -> str:
    return re.sub(r'[^A-Za-z0-9._-]', '_', str(s))


def build_qa_pairs_from_directory(
    base_path: str,
    json_path: Optional[str] = None,
    preview_count: int = 5,
) -> List[Dict[str, Any]]:
    """
    从 base_path 递归收集图片，结合 random_content.json 生成 llama 格式 QA 对。
    json_path 默认 base_path/random_content.json。
    返回 QA 对列表；不写文件。
    """
    base = Path(base_path).resolve()
    json_file = Path(json_path) if json_path else base / 'random_content.json'
    if not json_file.exists():
        json_file = base / 'random_content.json'
    if not json_file.exists():
        return []

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    group_dict: Dict[str, List[Dict]] = {}
    index_map: Dict[str, Dict] = {}
    groups = data.get('generated_groups', [])
    for idx, group in enumerate(groups, start=1):
        gid = group.get('group_id')
        contents = group.get('contents', [])
        group_dict[gid] = contents
        index_map[gid] = {
            'contents': contents,
            'sanitized': _sanitize(gid),
            'index_key': f'group_{idx}',
        }

    sanitized_map = {info['sanitized']: gid for gid, info in index_map.items()}
    indexkey_map = {info['index_key']: gid for gid, info in index_map.items()}

    image_files = []
    for p in base.rglob('*'):
        if p.is_file() and p.suffix.lower() in ('.jpg', '.jpeg', '.png'):
            image_files.append(p)

    result = []
    for image_file in image_files:
        stem = image_file.stem
        matched_gid = None
        if stem in group_dict:
            matched_gid = stem
        elif stem in sanitized_map:
            matched_gid = sanitized_map[stem]
        elif stem in indexkey_map:
            matched_gid = indexkey_map[stem]
        else:
            for gid in group_dict:
                if gid and gid in stem:
                    matched_gid = gid
                    break
        if not matched_gid:
            parent_name = image_file.parent.name
            if parent_name in group_dict:
                matched_gid = parent_name
            elif parent_name in sanitized_map:
                matched_gid = sanitized_map[parent_name]
            elif parent_name in indexkey_map:
                matched_gid = indexkey_map[parent_name]

        if not matched_gid:
            continue

        contents = group_dict.get(matched_gid, [])
        if not contents:
            continue

        rel_path = os.path.relpath(str(image_file), start=str(base)).replace('\\', '/')
        image_ref = f"./{rel_path}"

        for item in contents:
            label = item.get('label')
            text = item.get('text')
            if not text:
                continue
            qa_pair = {
                "images": [image_ref],
                "messages": [
                    {"role": "user", "content": f"<image>\n请提取这张结婚证中的{label}信息."},
                    {"role": "assistant", "content": text},
                ],
            }
            result.append(qa_pair)

    return result
