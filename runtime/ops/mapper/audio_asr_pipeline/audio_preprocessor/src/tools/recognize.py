#!/usr/bin/env python3
"""
语音识别脚本（tools 副本）
调用 WeNet 进行音频转文本，支持中英文。路径相对本脚本所在 src/tools 解析。
"""

import argparse
import subprocess
import sys
import threading
import queue
from pathlib import Path

# 从 src/utils 导入 color_utils
_TOOLS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _TOOLS_DIR.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src" / "utils"))

try:
    from color_utils import info, warning, error, ok, success, header
    def print_info(msg): print(info(msg))
    def print_warning(msg): print(warning(msg))
    def print_error(msg): print(error(msg))
    def print_ok(msg): print(ok(msg))
    def print_success(msg): print(success(msg))
    def print_header(msg): print(header(msg))
except ImportError:
    def print_info(msg): print(f"[INFO] {msg}")
    def print_warning(msg): print(f"[WARNING] {msg}")
    def print_error(msg): print(f"[ERROR] {msg}")
    def print_ok(msg): print(f"[OK] {msg}")
    def print_success(msg): print(f"[SUCCESS] {msg}")
    def print_header(msg): print(f"=== {msg} ===")


def get_project_root() -> Path:
    return _PROJECT_ROOT


def get_default_paths() -> dict:
    root = get_project_root()
    model_root = Path("/models/AudioOperations/asr")
    return {
        'audio_list': root / "output_data" / "normalization" / "item.list",
        'result_dir': root / "output_data" / "asr",
        'wenet_wrapper': root / "src" / "utils" / "run_wenet.py",
        'aishell_model': model_root / "aishell" / "final.pt",
        'librispeech_model': model_root / "librispeech" / "final.pt",
    }


def resolve_device(_device_arg: str) -> str:
    return "cpu"


def check_paths(paths: dict, language: str) -> None:
    if not paths['wenet_wrapper'].exists():
        raise FileNotFoundError(f"WeNet 包装器不存在: {paths['wenet_wrapper']}")
    if not paths['audio_list'].exists():
        raise FileNotFoundError(f"音频列表不存在: {paths['audio_list']}")
    paths['result_dir'].mkdir(parents=True, exist_ok=True)
    if language == "zh" and not paths['aishell_model'].exists():
        raise FileNotFoundError(f"AIShell 模型不存在: {paths['aishell_model']}")
    if language == "en" and not paths['librispeech_model'].exists():
        raise FileNotFoundError(f"LibriSpeech 模型不存在: {paths['librispeech_model']}")


def prepare_config(language: str) -> str:
    if language not in ("zh", "en"):
        raise ValueError(f"不支持的语言: {language}")
    model_dir = Path("/models/AudioOperations/asr") / ("aishell" if language == "zh" else "librispeech")
    yaml_files = list(model_dir.glob("*.yaml"))
    if not yaml_files:
        raise FileNotFoundError(f"未找到 YAML: {model_dir}")
    for f in yaml_files:
        if f.name == "train.yaml":
            return str(f)
    return str(yaml_files[0])


def read_output(stream, output_queue, stream_name):
    try:
        for line in iter(stream.readline, ''):
            if line:
                output_queue.put((stream_name, line.rstrip('\n')))
    except Exception:
        pass
    finally:
        stream.close()


def run_recognize(language: str, audio_list: str, result_dir: str, device: str) -> int:
    paths = get_default_paths()
    if audio_list:
        paths['audio_list'] = Path(audio_list).resolve()
    if result_dir:
        paths['result_dir'] = Path(result_dir).resolve()
    check_paths(paths, language)
    config_file = prepare_config(language)
    model_file = str(paths['aishell_model'] if language == "zh" else paths['librispeech_model'])
    actual_device = resolve_device(device)
    cmd = [
        sys.executable, str(paths['wenet_wrapper']),
        "--mode", "ctc_greedy_search", "--device", actual_device,
        "--config", config_file, "--test_data", str(paths['audio_list']),
        "--checkpoint", model_file, "--batch_size", "1",
        "--result_dir", str(paths['result_dir']),
    ]
    print_header("语音识别配置")
    print_info(f"语言: {language}")
    print_info(f"列表: {paths['audio_list']}  结果: {paths['result_dir']}")
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding='utf-8', bufsize=1, universal_newlines=True)
        output_queue = queue.Queue()
        for stream, name in [(process.stdout, 'stdout'), (process.stderr, 'stderr')]:
            t = threading.Thread(target=read_output, args=(stream, output_queue, name))
            t.daemon = True
            t.start()
        while True:
            try:
                _, line = output_queue.get(timeout=0.1)
                print(line)
            except queue.Empty:
                if process.poll() is not None:
                    try:
                        while True:
                            _, line = output_queue.get_nowait()
                            print(line)
                    except queue.Empty:
                        pass
                    break
        return_code = process.wait()
        print("-" * 80)
        if return_code == 0:
            print_success("语音识别完成！")
            return 0
        print_error(f"识别失败，返回码: {return_code}")
        return return_code
    except Exception as e:
        print_error(str(e))
        import traceback
        traceback.print_exc()
        return 1


def main():
    defaults = get_default_paths()
    parser = argparse.ArgumentParser(description="语音识别 - WeNet 音频转文本")
    parser.add_argument("--language", "-l", choices=["zh", "en"], default="zh")
    parser.add_argument("--audio_list", "-a", default=str(defaults['audio_list']))
    parser.add_argument("--result_dir", "-r", default=str(defaults['result_dir']))
    parser.add_argument("--device", "-d", default="cpu", help=argparse.SUPPRESS)
    args = parser.parse_args()
    print_header("语音识别")
    try:
        import torch
        print_info(f"PyTorch: {torch.__version__}")
    except ImportError:
        print_error("未安装 PyTorch")
        return 1
    if not defaults['wenet_wrapper'].exists():
        print_warning("WeNet 包装器不存在，请从 src/utils 运行或创建")
        return 1
    try:
        return run_recognize(args.language, args.audio_list, args.result_dir, args.device)
    except (ValueError, FileNotFoundError) as e:
        print_error(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
