import json
import os
import sys
from typing import Dict


def load_l1_cache(path: str) -> Dict[str, Dict[str, str]]:
    """
    读取已有的 l1_cache.json，并统一转换成:
        { name(str): {"std_name": str, "code": str}, ... }
    无文件或空文件时返回空 dict。
    """
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 支持历史格式：
    # 1) 直接就是 {name: code, ...}
    if isinstance(data, dict):
        mapping: Dict[str, Dict[str, str]] = {}
        for k, v in data.items():
            if k is None or v is None:
                continue
            name = str(k)
            code = str(v)
            mapping[name] = {"std_name": name, "code": code}
        return mapping

    # 2) [ {"name": "...", "code": "..."} 或 {"name": "...", "std_name": "...", "code": "..."} , ... ]
    if isinstance(data, list):
        mapping: Dict[str, Dict[str, str]] = {}
        for item in data:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            std_name = item.get("std_name") or name
            code = item.get("code")
            if name and code is not None:
                mapping[str(name)] = {
                    "std_name": str(std_name),
                    "code": str(code),
                }
        return mapping

    raise ValueError(f"不支持的 l1_cache 格式: {type(data)}")


def save_l1_cache(path: str, mapping: Dict[str, Dict[str, str]]) -> None:
    """
    将 {name: {"std_name": ..., "code": ...}} 形式的映射，保存为
        [ {"name": name, "std_name": std_name, "code": code}, ... ]
    便于人工查看和后续扩展。
    """
    items = [
        {
            "name": name,
            "std_name": value.get("std_name", name),
            "code": value.get("code"),
        }
        for name, value in sorted(mapping.items(), key=lambda kv: kv[0])
    ]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def collect_from_result(result_path: str) -> Dict[str, Dict[str, str]]:
    """
    从 main.py 输出的 result.json 中抽取:
        text -> {"std_name": normalized.std_name, "code": normalized.std_code}
    """
    with open(result_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("期望 main.py 输出为 JSON 数组(list) 格式")

    mapping: Dict[str, Dict[str, str]] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        normalized = item.get("normalized") or {}
        if not isinstance(normalized, dict):
            continue
        std_code = normalized.get("std_code")
        std_name = normalized.get("std_name")
        if text and std_code:
            # 这里按你的需求：
            #   name      = 原始 text
            #   std_name  = 归一化后的标准名称
            #   code      = 归一化后的编码
            mapping[str(text)] = {
                "std_name": str(std_name) if std_name is not None else str(text),
                "code": str(std_code),
            }

    return mapping


def main():
    if len(sys.argv) < 2:
        prog = os.path.basename(sys.argv[0]) or "update_l1cache.py"
        print(f"用法: python {prog} <main_result.json> [l1_cache_path]")
        print("  <main_result.json>: main.py 生成的 *_result.json 文件")
        print("  [l1_cache_path]:   l1_cache.json 路径，默认为 ../normalizer/l1_cache.json")
        sys.exit(1)

    result_path = sys.argv[1]
    if not os.path.exists(result_path):
        print(f"错误: 找不到输入文件 {result_path}")
        sys.exit(1)

    # 默认 l1_cache 路径：相对于当前脚本
    if len(sys.argv) >= 3:
        l1_cache_path = sys.argv[2]
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        l1_cache_path = os.path.join(script_dir, "..", "normalizer", "l1_cache.json")

    # 1. 读已有 l1_cache
    old_cache = load_l1_cache(l1_cache_path)

    # 2. 从 main 结果中收集新条目
    new_entries = collect_from_result(result_path)

    added, updated = 0, 0
    for name, entry in new_entries.items():
        if name not in old_cache:
            added += 1
        else:
            old_entry = old_cache[name]
            # 如果 std_name 或 code 有变化，都视为更新
            if (
                old_entry.get("std_name") != entry.get("std_name")
                or old_entry.get("code") != entry.get("code")
            ):
                updated += 1
        old_cache[name] = entry

    # 3. 写回 l1_cache
    os.makedirs(os.path.dirname(l1_cache_path), exist_ok=True)
    save_l1_cache(l1_cache_path, old_cache)

    print(f"更新完成: 新增 {added} 条, 覆盖 {updated} 条, 总计 {len(old_cache)} 条。")
    print(f"l1_cache 路径: {os.path.abspath(l1_cache_path)}")


if __name__ == "__main__":
    main()
