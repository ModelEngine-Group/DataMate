#!/usr/bin/env python3
"""
关键词召回率评估脚本

功能：
- 从 input_data/valiadation 下读取中英文关键词列表：
  - zh_keyword.txt（中文关键词，Kaldi 文本：utt_id<tab>kw1 kw2 ...）
  - en_keyword.txt（英文关键词，Kaldi 文本：utt_id<tab>kw1 kw2 ...）
- 从 output_data/asr/merged_text.txt 读取识别结果（每行: utt_id text...）
- 对 key 交集部分分别计算：
  - 中文关键词召回率
  - 英文关键词召回率

关键词召回率定义：
- 对于每个句子：
  - ref_keywords = 该句的关键词集合（去重）
  - hyp_tokens = ASR 识别结果按空格切分后的 token 集合（大小写不敏感）
  - hit = ref_keywords ∩ hyp_tokens 的元素个数
  - recall_utt = hit / len(ref_keywords)  （若该句没有关键词，则跳过）
- 整体召回率 = 所有可评估句子的 recall_utt 的平均值（macro 平均）

输出：
- 在 output_data/validation/keyword_recall.txt 中写入报告
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 颜色打印工具（与其他脚本风格保持一致）
sys.path.insert(0, str(PROJECT_ROOT / "src" / "utils"))
try:
    from color_utils import info, warning, error, ok, success, header  # type: ignore

    def print_info(msg: str):
        print(info(msg))

    def print_warning(msg: str):
        print(warning(msg))

    def print_error(msg: str):
        print(error(msg))

    def print_ok(msg: str):
        print(ok(msg))

    def print_success(msg: str):
        print(success(msg))

    def print_header(msg: str):
        print(header(msg))

except Exception:

    def print_info(msg: str):
        print(f"[INFO] {msg}")

    def print_warning(msg: str):
        print(f"[WARNING] {msg}")

    def print_error(msg: str):
        print(f"[ERROR] {msg}")

    def print_ok(msg: str):
        print(f"[OK] {msg}")

    def print_success(msg: str):
        print(f"[SUCCESS] {msg}")

    def print_header(msg: str):
        print(f"=== {msg} ===")


# YAML 配置加载（可选）
try:
    from yaml_config_loader import parse_args_with_yaml_config  # type: ignore
except Exception:
    parse_args_with_yaml_config = None  # type: ignore[assignment]


def read_kw_kaldi(path: Path) -> Dict[str, List[str]]:
    """
    读取关键词文件（Kaldi 风格，每行: key<tab或空格>kw1 kw2 ...）
    返回：key -> 关键词列表（按出现顺序，不去重）
    """
    data: Dict[str, List[str]] = {}
    if not path.exists():
        return data
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # 兼容 tab 或空格
            if "\t" in line:
                key, rest = line.split("\t", 1)
            else:
                parts = line.split(maxsplit=1)
                if len(parts) == 1:
                    key, rest = parts[0], ""
                else:
                    key, rest = parts
            if not key:
                continue
            kws = [w for w in rest.split() if w]
            data[key] = kws
    return data


def read_kv_text(path: Path) -> Dict[str, str]:
    """读取 Kaldi 风格文本（每行: key text...）"""
    data: Dict[str, str] = {}
    if not path.exists():
        return data
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            if not parts:
                continue
            key = parts[0]
            text = parts[1] if len(parts) > 1 else ""
            data[key] = text
    return data


def compute_keyword_recall_per_lang(
    kw_map: Dict[str, List[str]],
    hyp_map: Dict[str, str],
    lang_name: str,
    *,
    use_substring_match: bool = False,
) -> Tuple[float, int, int, List[Tuple[str, float, int, int, List[str], List[str]]]]:
    """
    计算单语种关键词召回率（macro 平均）。

    Returns:
        (
            overall_recall,
            num_utt_used,
            num_utt_total,
            per_utt_detail: [
                (utt_id, recall_utt, hit, ref_size, hit_list, miss_list)
            ],
        )
    """
    keys = set(kw_map.keys()) & set(hyp_map.keys())
    if not keys:
        print_warning(f"{lang_name} 无 key 交集，跳过该语种评估")
        return 0.0, 0, 0, []

    recalls: List[float] = []
    per_utt: List[Tuple[str, float, int, int, List[str], List[str]]] = []
    num_total = 0
    for k in sorted(keys):
        ref_kws = [w for w in kw_map.get(k, []) if w]
        num_total += 1
        if not ref_kws:
            # 该句没有关键词，跳过，不计入分母
            continue
        ref_set: Set[str] = {w.lower() for w in ref_kws}

        hyp_text = hyp_map.get(k, "")
        if use_substring_match:
            # 适用于中文：关键词是词，识别结果通常是连续文本
            hyp_text_lower = hyp_text.lower()
            hit_words = [w for w in ref_set if w and w in hyp_text_lower]
            miss_words = [w for w in ref_set if w not in hyp_text_lower]
        else:
            # 适用于英文：按空格分词
            hyp_tokens = [t.lower() for t in hyp_text.split() if t]
            hyp_set: Set[str] = set(hyp_tokens)
            hit_words = [w for w in ref_set if w in hyp_set]
            miss_words = [w for w in ref_set if w not in hyp_set]

        if not ref_set:
            continue

        hit = len(hit_words)
        recall_utt = hit / float(len(ref_set))
        recalls.append(recall_utt)
        per_utt.append(
            (
                k,
                recall_utt,
                hit,
                len(ref_set),
                sorted(hit_words),
                sorted(miss_words),
            )
        )

    if not recalls:
        print_warning(f"{lang_name} 中没有可评估的含关键词样本")
        return 0.0, 0, num_total, per_utt

    overall = sum(recalls) / len(recalls)
    return overall, len(recalls), num_total, per_utt


def main() -> int:
    parser = argparse.ArgumentParser(
        description="评估 ASR 在中英文关键词上的召回率",
    )
    parser.add_argument(
        "--config",
        "-c",
        default=None,
        help="YAML 配置文件路径（可选）。支持写 eval_keyword_recall: {...}",
    )
    parser.add_argument(
        "--zh_kw",
        default=str(
            PROJECT_ROOT / "input_data" / "valiadation" / "zh_keyword.txt"
        ),
        help="中文关键词文件（Kaldi 文本格式: utt kw1 kw2 ...）",
    )
    parser.add_argument(
        "--en_kw",
        default=str(
            PROJECT_ROOT / "input_data" / "valiadation" / "en_keyword.txt"
        ),
        help="英文关键词文件（Kaldi 文本格式: utt kw1 kw2 ...）",
    )
    parser.add_argument(
        "--hyp",
        default=str(PROJECT_ROOT / "output_data" / "asr" / "merged_text.txt"),
        help="ASR 识别结果（Kaldi 文本格式: utt words...）",
    )
    parser.add_argument(
        "--work_dir",
        default=str(PROJECT_ROOT / "output_data" / "validation"),
        help="报告输出目录，默认: output_data/validation",
    )

    if parse_args_with_yaml_config:
        args = parse_args_with_yaml_config(
            parser,
            section="eval_keyword_recall",
            default_config_paths=[PROJECT_ROOT / "config" / "eval_keyword_recall.yaml"],
        )
    else:
        args = parser.parse_args()

    zh_kw_path = Path(args.zh_kw)
    en_kw_path = Path(args.en_kw)
    hyp_path = Path(args.hyp)
    work_dir = Path(args.work_dir)

    print_header("ASR 关键词召回率评估")

    if not hyp_path.exists():
        print_error(f"识别结果不存在: {hyp_path}")
        return 1

    zh_kw = read_kw_kaldi(zh_kw_path)
    en_kw = read_kw_kaldi(en_kw_path)
    hyp = read_kv_text(hyp_path)

    if not zh_kw and not en_kw:
        print_error(f"未找到关键词文件: {zh_kw_path} / {en_kw_path}")
        return 1

    zh_recall, zh_utt_used, zh_utt_total, zh_detail = compute_keyword_recall_per_lang(
        zh_kw, hyp, "中文", use_substring_match=True
    )
    en_recall, en_utt_used, en_utt_total, en_detail = compute_keyword_recall_per_lang(
        en_kw, hyp, "英文", use_substring_match=False
    )

    if zh_utt_used > 0:
        print_ok(
            f"中文关键词召回率: {zh_recall * 100:.2f}% "
            f"(含关键词样本 {zh_utt_used} 条 / 全部交集样本 {zh_utt_total} 条)"
        )
    else:
        print_warning("中文无可评估关键词样本")

    if en_utt_used > 0:
        print_ok(
            f"英文关键词召回率: {en_recall * 100:.2f}% "
            f"(含关键词样本 {en_utt_used} 条 / 全部交集样本 {en_utt_total} 条)"
        )
    else:
        print_warning("英文无可评估关键词样本")

    # 输出报告（包含明细）
    work_dir.mkdir(parents=True, exist_ok=True)
    report_path = work_dir / "keyword_recall.txt"
    with report_path.open("w", encoding="utf-8") as f:
        f.write("ASR 关键词召回率评估报告\n")
        f.write(f"中文关键词: {zh_kw_path}\n")
        f.write(f"英文关键词: {en_kw_path}\n")
        f.write(f"识别结果: {hyp_path}\n\n")

        f.write(
            f"中文：交集样本总数 = {zh_utt_total}，"
            f"含关键词样本数 = {zh_utt_used}，"
            f"关键词召回率 = {zh_recall * 100:.2f}%\n"
        )
        f.write(
            f"英文：交集样本总数 = {en_utt_total}，"
            f"含关键词样本数 = {en_utt_used}，"
            f"关键词召回率 = {en_recall * 100:.2f}%\n"
        )
        f.write("\n")

        def dump_lang_detail(
            lang_title: str,
            details: List[Tuple[str, float, int, int, List[str], List[str]]],
        ) -> None:
            f.write(f"==== {lang_title} 逐句明细 ====\n")
            if not details:
                f.write("（无可评估样本）\n\n")
                return
            for (
                utt_id,
                recall_utt,
                hit,
                ref_size,
                hit_words,
                miss_words,
            ) in details:
                f.write(f"utt_id: {utt_id}\n")
                f.write(
                    f"  recall: {recall_utt * 100:.2f}% "
                    f"(hit={hit}, ref_kw={ref_size})\n"
                )
                f.write(f"  hit_kw: {' '.join(hit_words) if hit_words else 'None'}\n")
                f.write(
                    f"  miss_kw: {' '.join(miss_words) if miss_words else 'None'}\n\n"
                )

        dump_lang_detail("中文", zh_detail)
        dump_lang_detail("英文", en_detail)

    print_success(f"评估完成，报告已写入: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

