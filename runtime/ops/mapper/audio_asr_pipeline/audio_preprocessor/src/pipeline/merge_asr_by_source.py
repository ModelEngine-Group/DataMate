#!/usr/bin/env python3
"""
读取 split 阶段的 item_with_lang.list 与 zh/en 两次 ASR 的 text 结果，
按 source_key + segment_index 合并为每条原音频一句完整文本。
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# YAML 配置加载（可选）
sys.path.insert(0, str(_PROJECT_ROOT / "src" / "utils"))
try:
    from yaml_config_loader import parse_args_with_yaml_config  # type: ignore
except Exception:
    parse_args_with_yaml_config = None  # type: ignore[assignment]


def load_key_to_text(text_path: Path) -> Dict[str, str]:
    """WeNet 的 result_dir/mode/text 每行: key 空格 文本"""
    out: Dict[str, str] = {}
    if not text_path.exists():
        return out
    with text_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            key = parts[0]
            text = parts[1] if len(parts) > 1 else ""
            out[key] = text
    return out


def merge_once(list_file: Path, zh_text: Path, en_text: Path, output: Path) -> int:
    """核心合并逻辑，供 main 与其他脚本复用。"""
    if not list_file.exists():
        print(f"[ERROR] 列表不存在: {list_file}", file=sys.stderr)
        return 1

    items: List[Dict] = []
    with list_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))

    zh_map = load_key_to_text(zh_text)
    en_map = load_key_to_text(en_text)
    key_to_text: Dict[str, str] = {**zh_map, **en_map}

    # 按 source_key 分组，按 segment_index 排序后拼接
    by_source: Dict[str, List[tuple]] = defaultdict(list)
    for it in items:
        key = it.get("key", "")
        source = it.get("source_key", key)
        seg_idx = it.get("segment_index", 0)
        text = key_to_text.get(key, "")
        by_source[source].append((seg_idx, text))

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        for source in sorted(by_source.keys()):
            parts = sorted(by_source[source], key=lambda x: x[0])
            full_text = " ".join(t.strip() for _, t in parts if t.strip())
            f.write(f"{source} {full_text}\n")

    print(f"[OK] 已合并 {len(by_source)} 条原音频 -> {output}")
    return 0


def main_for_api(list_file: Path, zh_text: Path, en_text: Path, output: Path) -> int:
    """供其他模块直接调用的 API 包装。"""
    return merge_once(list_file, zh_text, en_text, output)


def main() -> int:
    parser = argparse.ArgumentParser(description="按 source_key 合并子片段 ASR 结果")
    parser.add_argument(
        "--config",
        "-c",
        default=None,
        help="YAML 配置文件路径（可选）。支持写 merge_asr_by_source: {list_file:..., output:...} 或直接顶层同名键",
    )
    parser.add_argument(
        "--list_file",
        default=str(_PROJECT_ROOT / "output_data" / "split" / "item_with_lang.list"),
        help="split 输出的 list（含 source_key, segment_index）",
    )
    parser.add_argument(
        "--zh_text",
        default=str(_PROJECT_ROOT / "output_data" / "asr" / "zh" / "ctc_greedy_search" / "text"),
        help="中文 ASR 结果 text 文件",
    )
    parser.add_argument(
        "--en_text",
        default=str(_PROJECT_ROOT / "output_data" / "asr" / "en" / "ctc_greedy_search" / "text"),
        help="英文 ASR 结果 text 文件",
    )
    parser.add_argument(
        "--output",
        default=str(_PROJECT_ROOT / "output_data" / "asr" / "merged_text.txt"),
        help="合并后输出：每行 source_key 空格 整段文本",
    )
    if parse_args_with_yaml_config:
        args = parse_args_with_yaml_config(
            parser,
            section="merge_asr_by_source",
            default_config_paths=[_PROJECT_ROOT / "config" / "merge_asr_by_source.yaml"],
        )
    else:
        args = parser.parse_args()

    return merge_once(
        list_file=Path(args.list_file),
        zh_text=Path(args.zh_text),
        en_text=Path(args.en_text),
        output=Path(args.output),
    )


if __name__ == "__main__":
    sys.exit(main())
