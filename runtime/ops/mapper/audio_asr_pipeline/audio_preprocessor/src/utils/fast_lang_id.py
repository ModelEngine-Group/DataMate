#!/usr/bin/env python3
"""
超快速中英语言识别（LID）

读取 generate_audio_list.py 生成的 item.list(jsonl) 或直接扫描目录中的音频文件，
使用 DataMate 运行环境中的 SpeechBrain 预训练 LID 模型做语言识别，并输出带 lang 字段的 jsonl。

设计目标：
- 极快：默认只取音频前几秒做判断
- 批处理：减少模型调用开销
- 仅中英二分类：识别结果为 zh（中文）或 en（英文），其他语言统一归为 en
"""

import argparse
import json
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


# 添加脚本所在目录到系统路径，导入颜色工具（保持与 generate_audio_list.py 一致的风格）
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "audio_convert"))
    from color_utils import info, warning, error, ok, success, header  # type: ignore
except Exception:
    def info(msg: str) -> str:
        return f"[INFO] {msg}"

    def warning(msg: str) -> str:
        return f"[WARNING] {msg}"

    def error(msg: str) -> str:
        return f"[ERROR] {msg}"

    def ok(msg: str) -> str:
        return f"[OK] {msg}"

    def success(msg: str) -> str:
        return f"[SUCCESS] {msg}"

    def header(msg: str) -> str:
        return f"=== {msg} ==="

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
else:
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


def _project_root() -> Path:
    return Path(__file__).parent.parent.parent


def _ensure_speechbrain_on_path() -> None:
    """SpeechBrain is provided by the DataMate runtime environment."""
    return None


def _patch_yaml_loader_max_depth() -> None:
    """兼容部分 PyYAML/HyperPyYAML 组合缺失 Loader.max_depth 的问题。"""
    try:
        import yaml  # type: ignore

        for name in ("Loader", "SafeLoader", "FullLoader", "UnsafeLoader"):
            loader = getattr(yaml, name, None)
            if loader is not None and not hasattr(loader, "max_depth"):
                setattr(loader, "max_depth", 1000)
    except Exception:
        pass
    try:
        import ruamel.yaml  # type: ignore

        for name in ("Loader", "SafeLoader", "RoundTripLoader", "BaseLoader"):
            loader = getattr(ruamel.yaml, name, None)
            if loader is not None and not hasattr(loader, "max_depth"):
                setattr(loader, "max_depth", 1000)
    except Exception:
        pass


def _find_audio_files(audio_dir: Path) -> List[Path]:
    patterns = ["*.wav", "*.WAV", "*.flac", "*.FLAC", "*.mp3", "*.MP3", "*.aac", "*.AAC", "*.m4a", "*.M4A"]
    files: List[Path] = []
    for pat in patterns:
        files.extend(audio_dir.rglob(pat))
    return sorted(set(files))


def _load_jsonl_items(path: Path, filter_ok_only: bool = False) -> List[Dict]:
    items: List[Dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))

    if not filter_ok_only:
        return items

    filtered = [it for it in items if it.get("quality_flag", "ok") == "ok"]
    if not items:
        return items
    print_info(f"质量过滤后保留 {len(filtered)}/{len(items)} 条，仅识别 quality_flag=='ok' 的音频")
    return filtered


def _dump_jsonl_items(path: Path, items: Iterable[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")


def _iso_to_zh_en(lid_label: str) -> str:
    """
    将 LID 模型输出映射为仅两种：zh（中文）或 en（英文）。
    模型可能返回 "en: English"、"zh: Chinese" 等，取冒号前作为语言码再判断。
    中文相关 ISO 码映射为 zh，其余一律为 en。
    """
    raw = (lid_label or "").strip()
    if ":" in raw:
        iso = raw.split(":", 1)[0].strip().lower()
    else:
        iso = raw.lower()
    zh_aliases = {"zh", "cmn", "yue", "wuu", "nan", "cdo", "cjy", "hsn", "hak"}
    if iso in zh_aliases:
        return "zh"
    return "en"


def _out_item(it: Dict, lang: str) -> Dict:
    """只保留 key、wav、txt、lang 四列，供输出 jsonl 使用。"""
    return {
        "key": it.get("key", ""),
        "wav": it.get("wav") or it.get("audio") or it.get("path", ""),
        "txt": it.get("txt", ""),
        "lang": lang,
    }


def _batch_iter(xs: List[Dict], batch_size: int) -> Iterable[List[Dict]]:
    for i in range(0, len(xs), batch_size):
        yield xs[i : i + batch_size]


def _lid_predict_items(
    items: List[Dict],
    model_source: str,
    model_savedir: Path,
    device: str,
    batch_size: int,
    max_seconds: float,
) -> List[Dict]:
    _ensure_speechbrain_on_path()
    _patch_yaml_loader_max_depth()

    # 这里延迟导入，避免只跑 --help 时加载 torch/torchaudio
    import torch  # type: ignore
    from types import SimpleNamespace

    # 兼容旧版 torch：SpeechBrain 可能会引用 torch.amp.custom_fwd/custom_bwd
    # - torch>=2.0: torch.amp.custom_fwd/custom_bwd（支持 device_type 等参数）
    # - torch<2.0: torch.cuda.amp.custom_fwd/custom_bwd（签名可能更旧，不支持 device_type）
    try:
        has_amp = hasattr(torch, "amp")
        has_custom_fwd = has_amp and hasattr(torch.amp, "custom_fwd")
        has_custom_bwd = has_amp and hasattr(torch.amp, "custom_bwd")
        if not (has_custom_fwd and has_custom_bwd):
            try:
                from torch.cuda.amp import custom_fwd as _custom_fwd  # type: ignore
                from torch.cuda.amp import custom_bwd as _custom_bwd  # type: ignore
            except Exception:
                # 退化为 no-op 装饰器（不启用 AMP 也能推理）
                def _custom_fwd(*_args, **_kwargs):  # type: ignore
                    def _decorator(fn):
                        return fn

                    return _decorator

                def _custom_bwd(*_args, **_kwargs):  # type: ignore
                    def _decorator(fn):
                        return fn

                    return _decorator

            if not hasattr(torch, "amp"):
                torch.amp = SimpleNamespace()  # type: ignore[attr-defined]

            def _drop_unsupported_kwargs(deco):  # type: ignore
                def _wrapped(*args, **kwargs):
                    # 旧版 deco 可能不支持 device_type 等 kwargs；这里直接丢弃所有 kwargs
                    # 保证能作为装饰器正常使用
                    return deco(*args)

                return _wrapped

            torch.amp.custom_fwd = _drop_unsupported_kwargs(_custom_fwd)  # type: ignore[attr-defined]
            torch.amp.custom_bwd = _drop_unsupported_kwargs(_custom_bwd)  # type: ignore[attr-defined]
    except Exception:
        # 不让兼容逻辑影响主流程；真正的导入错误会在后面暴露
        pass

    from speechbrain.inference.classifiers import EncoderClassifier  # type: ignore

    # 使用本地目录：/abs/path/to/model_dir
    src_path = Path(model_source)
    is_local_dir = src_path.exists() and src_path.is_dir()
    resolved_source = str(src_path.resolve()) if is_local_dir else model_source

    overrides = {}
    if is_local_dir:
        # hyperparams.yaml 里的 pretrained_path 可能不是本地路径，这里强制指向本地目录。
        overrides = {"pretrained_path": resolved_source}

        # 预先检查必需权重是否存在，避免长时间卡在 fetch/重试
        required = ["hyperparams.yaml", "label_encoder.txt", "embedding_model.ckpt", "classifier.ckpt"]
        missing = [fn for fn in required if not (src_path / fn).exists()]
        if missing:
            raise RuntimeError(
                "本地 LID 模型目录不完整，缺少必要文件：\n"
                + "\n".join([f"- {src_path / fn}" for fn in missing])
                + "\n\n请检查本地模型目录是否完整。"
            )
    device = "cpu"
    try:
        classifier = EncoderClassifier.from_hparams(
            source=resolved_source,
            savedir=str(model_savedir),
            run_opts={"device": device},
            overrides=overrides,
        )
    except Exception as e:
        raise RuntimeError(
            "加载 SpeechBrain LID 模型失败。\n"
            f"- source={model_source}\n"
            f"- savedir={model_savedir}\n"
            f"- error={type(e).__name__}: {e}"
        ) from e

    out_items: List[Dict] = []
    total = len(items)
    done = 0

    for batch in _batch_iter(items, batch_size):
        wav_tensors: List[torch.Tensor] = []
        wav_lens: List[float] = []
        ok_mask: List[bool] = []

        for it in batch:
            wav_path = it.get("wav") or it.get("audio") or it.get("path")
            if not wav_path:
                ok_mask.append(False)
                continue
            try:
                sig = classifier.load_audio(str(wav_path))
                # sig: [time] 或 [channels, time]，speechbrain load_audio 通常返回 [time]
                if sig.ndim > 1:
                    sig = sig.mean(dim=0)
                if max_seconds > 0:
                    max_samples = int(16000 * max_seconds)
                    sig = sig[:max_samples]
                if sig.numel() == 0:
                    ok_mask.append(False)
                    continue
                wav_tensors.append(sig)
                wav_lens.append(float(sig.shape[0]))
                ok_mask.append(True)
            except Exception:
                ok_mask.append(False)

        if not wav_tensors:
            for it in batch:
                out_items.append(_out_item(it, "en"))
            done += len(batch)
            continue

        max_len = max(int(x.shape[0]) for x in wav_tensors)
        padded = torch.zeros((len(wav_tensors), max_len), dtype=torch.float32)
        lens_rel = torch.zeros((len(wav_tensors),), dtype=torch.float32)
        for i, sig in enumerate(wav_tensors):
            L = int(sig.shape[0])
            padded[i, :L] = sig.float()
            lens_rel[i] = float(L) / float(max_len) if max_len > 0 else 1.0

        with torch.inference_mode():
            out_prob, score, index, text_lab = classifier.classify_batch(padded, lens_rel)

        pred_i = 0
        for it, ok_ in zip(batch, ok_mask):
            if not ok_:
                out_items.append(_out_item(it, "en"))
            else:
                lid_label = str(text_lab[pred_i]) if isinstance(text_lab, list) else str(text_lab)
                lang = _iso_to_zh_en(lid_label)
                out_items.append(_out_item(it, lang))
                pred_i += 1

        done += len(batch)
        if done % max(10, batch_size) == 0 or done == total:
            print_info(f"LID 进度: {done}/{total}")

    return out_items


def parse_arguments():
    default_models_dir = _project_root() / "models" / "lid"
    default_local_model_dir = default_models_dir / "speechbrain_lang-id-voxlingua107-ecapa"
    default_savedir = default_models_dir / "_speechbrain_cache" / "lang-id-voxlingua107-ecapa"
    default_audio_dir = _project_root() / "output_data" / "denoise"
    default_quality_list = _project_root() / "output_data" / "denoise" / "item_with_quality.list"
    default_output = _project_root() / "output_data" / "lid" / "item_with_lang.list"

    parser = argparse.ArgumentParser(
        description="超快速中英语言识别（SpeechBrain），仅输出 zh/en",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=rf"""
示例:
  # 默认：直接扫描 output_data/denoise 下所有音频
  python -m src.utils.fast_lang_id

  # 启用质量过滤：默认读取 item_with_quality.list，并且仅识别 ok 音频
  python -m src.utils.fast_lang_id --filter-audio=True

  # 启用质量过滤，但自定义过滤列表路径
  python -m src.utils.fast_lang_id --filter-audio=True --filter-audio-list ./somewhere/item_with_quality.list

  # 显式指定输入列表
  python -m src.utils.fast_lang_id --input_list ./output_data/denoise/item.list
        """,
    )

    g = parser.add_mutually_exclusive_group(required=False)
    g.add_argument(
        "--input_list",
        "-i",
        default=None,
        help="输入列表文件（jsonl，每行包含 wav 字段；若包含 quality_flag 字段则仅使用 quality_flag=='ok' 的条目）",
    )
    g.add_argument("--audio_dir", "-a", default=str(default_audio_dir), help=f"直接扫描目录下音频文件，默认: {default_audio_dir}")

    parser.add_argument("--output", "-o", default=str(default_output), help=f"输出列表文件路径，默认: {default_output}")
    parser.add_argument(
        "--filter-audio",
        default="False",
        help="是否启用质量过滤；True 时默认读取 item_with_quality.list 并只识别 ok 音频",
    )
    parser.add_argument(
        "--filter-audio-list",
        default=str(default_quality_list),
        help=f"质量过滤列表路径，默认: {default_quality_list}",
    )
    parser.add_argument(
        "--model_source",
        default=str(default_local_model_dir),
        help="SpeechBrain LID 本地模型目录。",
    )
    parser.add_argument("--model_savedir", default=str(default_savedir), help=f"模型缓存目录，默认: {default_savedir}")
    parser.add_argument("--device", default="cpu", help=argparse.SUPPRESS)
    parser.add_argument("--batch_size", type=int, default=8, help="批大小（越大越快，但更吃内存）")
    parser.add_argument("--max_seconds", type=float, default=3.0, help="只取音频前 N 秒做判断，0 表示全长")

    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    print_header("快速语言识别（LID）")

    output_path = Path(args.output).resolve()
    model_savedir = Path(args.model_savedir).resolve()
    filter_audio = str(args.filter_audio).lower() in {"1", "true", "yes", "y", "on"}
    filter_audio_list = Path(args.filter_audio_list).resolve()

    # 读入 items（默认使用 output_data/normalization 目录）
    items: List[Dict]
    if args.input_list:
        input_path = Path(args.input_list).resolve()
        if not input_path.exists():
            print_error(f"输入列表不存在: {input_path}")
            return 1
        print_info(f"输入列表: {input_path}")
        items = _load_jsonl_items(input_path)
        if filter_audio:
            items = [it for it in items if it.get("quality_flag", "ok") == "ok"]
    else:
        if filter_audio:
            if filter_audio_list.exists():
                print_info(f"启用质量过滤，读取列表: {filter_audio_list}")
                items = _load_jsonl_items(filter_audio_list, filter_ok_only=True)
            else:
                print_warning(f"质量过滤列表不存在，回退为扫描目录: {filter_audio_list}")
                audio_dir = Path(args.audio_dir).resolve()
                if not audio_dir.exists():
                    print_error(f"音频目录不存在: {audio_dir}")
                    return 1
                print_info(f"扫描目录: {audio_dir}")
                audio_files = _find_audio_files(audio_dir)
                if not audio_files:
                    print_warning("未找到任何音频文件")
                    return 0
                items = [{"key": p.stem, "wav": str(p.resolve()), "txt": ""} for p in audio_files]
        else:
            audio_dir = Path(args.audio_dir).resolve()
            if not audio_dir.exists():
                print_error(f"音频目录不存在: {audio_dir}")
                return 1
            print_info(f"扫描目录: {audio_dir}")
            audio_files = _find_audio_files(audio_dir)
            if not audio_files:
                print_warning("未找到任何音频文件")
                return 0
            items = [{"key": p.stem, "wav": str(p.resolve()), "txt": ""} for p in audio_files]

    if not items:
        print_warning("输入为空，退出")
        return 0

    print_info(f"待识别音频数: {len(items)}")
    print_info(f"模型: {args.model_source}")
    print_info(f"模型缓存目录: {model_savedir}")
    print_info(f"batch_size={args.batch_size}, max_seconds={args.max_seconds}")

    try:
        out_items = _lid_predict_items(
            items=items,
            model_source=args.model_source,
            model_savedir=model_savedir,
            device="cpu",
            batch_size=max(1, int(args.batch_size)),
            max_seconds=float(args.max_seconds),
        )
    except Exception as e:
        print_error(f"LID 推理失败: {e}")
        print_error("traceback:\n" + traceback.format_exc())
        return 1

    _dump_jsonl_items(output_path, out_items)
    print_success(f"完成！输出: {output_path}")

    stat: Dict[str, int] = {"zh": 0, "en": 0}
    for it in out_items:
        stat[str(it.get("lang", "en"))] = stat.get(str(it.get("lang", "en")), 0) + 1
    print_info(f"统计: zh={stat.get('zh', 0)}, en={stat.get('en', 0)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
