#!/usr/bin/env python3
"""
WER 评估脚本

功能：
- 从 input_data/validation 下读取参考转写：
  - zh_transcript.txt（中文，按“字错率”评估）
  - en_transcript.txt（英文，按“词错率”评估）
- 从 output_data/asr/merged_text.txt 读取识别结果（每行: key text...）
- 对 key 交集部分分别计算：
  - 中文：char 模式下的错字率
  - 英文：word 模式下的 WER

注意：
- 自动跳过只在其中一边存在的 key（既不在 ref 也不在 hyp 的样本）
- 依赖 src/utils/compute_wer.py 中的 compute-wer 实现
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, Set, Tuple


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


def read_kv(path: Path) -> Dict[str, str]:
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


def dump_subset(path: Path, data: Dict[str, str], keys: Set[str]) -> None:
    """将指定 key 子集写出为 Kaldi 风格文本文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for k in sorted(keys):
            f.write(f"{k} {data.get(k, '').strip()}\n")


def run_compute_wer(ref: Path, hyp: Path, char_mode: bool) -> Tuple[float, str]:
    """
    调用 src/utils/compute_wer.py 计算错率。

    Args:
        ref: 参考转写文件路径
        hyp: 识别结果文件路径
        char_mode: True=按字符（适合中文），False=按词（适合英文）

    Returns:
        (整体错误率, compute_wer 原始输出字符串)
    """
    script = PROJECT_ROOT / "src" / "utils" / "compute_wer.py"
    if not script.exists():
        raise FileNotFoundError(f"未找到 compute_wer.py: {script}")

    # --char=1 开启逐字符评估；--char=0 为逐词
    char_flag = "1" if char_mode else "0"
    cmd = [
        sys.executable,
        str(script),
        f"--char={char_flag}",
        str(ref),
        str(hyp),
    ]
    proc = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8"
    )
    if proc.returncode != 0:
        raise RuntimeError(f"compute_wer 运行失败: {proc.stderr}")

    overall = 0.0
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("Overall ->"):
            # 形如: Overall ->  6.46 % N=...，取中间的百分比
            try:
                percent_str = line.split("->", 1)[1].split("%", 1)[0].strip()
                overall = float(percent_str)
            except Exception:
                pass
    return overall, proc.stdout


def main() -> int:
    parser = argparse.ArgumentParser(
        description="评估中英文 ASR 错误率（中文字错率，英文词错率）",
    )
    parser.add_argument(
        "--config",
        "-c",
        default=None,
        help="YAML 配置文件路径（可选）。支持写 eval_wer: {zh_ref:..., hyp:..., work_dir:...} 或直接顶层同名键",
    )
    parser.add_argument(
        "--zh_ref",
        default=str(PROJECT_ROOT / "input_data" / "validation" / "zh_transcript.txt"),
        help="中文参考转写（Kaldi 文本格式）",
    )
    parser.add_argument(
        "--en_ref",
        default=str(PROJECT_ROOT / "input_data" / "validation" / "en_transcript.txt"),
        help="英文参考转写（Kaldi 文本格式）",
    )
    parser.add_argument(
        "--hyp",
        default=str(PROJECT_ROOT / "output_data" / "asr" / "merged_text.txt"),
        help="识别结果文本（merged_text.txt）",
    )
    parser.add_argument(
        "--work_dir",
        default=str(PROJECT_ROOT / "output_data" / "validation"),
        help="中间文件输出目录，默认: output_data/validation",
    )
    if parse_args_with_yaml_config:
        args = parse_args_with_yaml_config(
            parser,
            section="eval_wer",
            default_config_paths=[PROJECT_ROOT / "config" / "eval_wer.yaml"],
        )
    else:
        args = parser.parse_args()

    zh_ref_path = Path(args.zh_ref)
    en_ref_path = Path(args.en_ref)
    hyp_path = Path(args.hyp)
    work_dir = Path(args.work_dir)

    print_header("ASR 错误率评估")

    # 兼容历史目录名拼写：valiadation（用户侧数据目录存在该拼写）
    # - CLI/YAML 可能给绝对路径或相对路径，这里都做回退
    default_zh_abs = PROJECT_ROOT / "input_data" / "validation" / "zh_transcript.txt"
    default_en_abs = PROJECT_ROOT / "input_data" / "validation" / "en_transcript.txt"
    fallback_zh_abs = PROJECT_ROOT / "input_data" / "valiadation" / "zh_transcript.txt"
    fallback_en_abs = PROJECT_ROOT / "input_data" / "valiadation" / "en_transcript.txt"

    def maybe_fallback_validation_typo(p: Path, fallback_abs: Path) -> Path:
        if p.exists():
            return p
        # 1) 传入的是默认绝对路径
        if str(p) == str(default_zh_abs) or str(p) == str(default_en_abs):
            return fallback_abs if fallback_abs.exists() else p
        # 2) 传入的是相对路径：input_data/validation/*.txt
        if p.as_posix().endswith("input_data/validation/" + p.name):
            return fallback_abs if fallback_abs.exists() else p
        # 3) 传入的是单纯相对：validation/*.txt（防呆）
        if "validation" in p.parts and p.name in ("zh_transcript.txt", "en_transcript.txt"):
            return fallback_abs if fallback_abs.exists() else p
        return p

    zh_ref_path = maybe_fallback_validation_typo(zh_ref_path, fallback_zh_abs)
    en_ref_path = maybe_fallback_validation_typo(en_ref_path, fallback_en_abs)

    if not hyp_path.exists():
        print_error(f"识别结果不存在: {hyp_path}")
        return 1

    zh_ref = read_kv(zh_ref_path)
    en_ref = read_kv(en_ref_path)
    hyp = read_kv(hyp_path)

    if not zh_ref and not en_ref:
        print_error(f"未找到参考转写: {zh_ref_path} / {en_ref_path}")
        return 1

    # 计算交集，自动跳过单边缺失的样本
    zh_keys = set(zh_ref.keys()) & set(hyp.keys())
    en_keys = set(en_ref.keys()) & set(hyp.keys())

    print_info(f"中文样本交集: {len(zh_keys)} 条")
    print_info(f"英文样本交集: {len(en_keys)} 条")

    zh_ref_sub = work_dir / "zh_ref.txt"
    zh_hyp_sub = work_dir / "zh_hyp.txt"
    en_ref_sub = work_dir / "en_ref.txt"
    en_hyp_sub = work_dir / "en_hyp.txt"

    zh_wer = None
    en_wer = None
    zh_detail = ""
    en_detail = ""

    if zh_keys:
        dump_subset(zh_ref_sub, zh_ref, zh_keys)
        dump_subset(zh_hyp_sub, hyp, zh_keys)
        zh_wer, zh_detail = run_compute_wer(zh_ref_sub, zh_hyp_sub, char_mode=True)
        print_ok(f"中文字错率 (CER): {zh_wer:.2f}%")
    else:
        print_warning("无中文样本交集，跳过中文评估")

    if en_keys:
        dump_subset(en_ref_sub, en_ref, en_keys)
        dump_subset(en_hyp_sub, hyp, en_keys)
        en_wer, en_detail = run_compute_wer(en_ref_sub, en_hyp_sub, char_mode=False)
        print_ok(f"英文词错率 (WER): {en_wer:.2f}%")
    else:
        print_warning("无英文样本交集，跳过英文评估")

    # 输出最终识别报告
    report_dir = work_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "transcript_log.txt"
    with report_path.open("w", encoding="utf-8") as f:
        f.write("ASR 验证集评估报告\n")
        f.write(f"中文参考: {zh_ref_path}\n")
        f.write(f"英文参考: {en_ref_path}\n")
        f.write(f"识别结果: {hyp_path}\n\n")
        f.write(f"中文样本交集: {len(zh_keys)} 条\n")
        f.write(f"英文样本交集: {len(en_keys)} 条\n\n")
        if zh_wer is not None:
            f.write(f"中文字错率 (CER): {zh_wer:.2f}%\n")
        else:
            f.write("中文字错率 (CER): 无可评估样本\n")
        if en_wer is not None:
            f.write(f"英文词错率 (WER): {en_wer:.2f}%\n")
        else:
            f.write("英文词错率 (WER): 无可评估样本\n")

        if zh_detail:
            f.write(zh_detail.strip() + "\n")
        else:
            f.write("（无可评估样本）\n")

        if en_detail:
            f.write(en_detail.strip() + "\n")
        else:
            f.write("（无可评估样本）\n")

    print_success(f"评估完成，报告已写入: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

