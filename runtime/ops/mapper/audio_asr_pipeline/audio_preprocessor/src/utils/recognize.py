#!/usr/bin/env python3
"""
语音识别脚本
调用 WeNet 模型进行音频转文本识别
支持中文和英文，自动选择设备
"""

import argparse
import json
import subprocess
import sys
import threading
import queue
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 当前在 src/utils，同目录导入 color_utils（相对路径以项目根为基准）
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

try:
    from color_utils import (
        info, warning, error, ok, success, header
    )

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

except ImportError:
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


def get_project_root() -> Path:
    """项目根目录（src/utils -> src -> 根）。"""
    return Path(__file__).resolve().parent.parent.parent


def check_npu_available() -> bool:
    try:
        import torch_npu
        return True
    except ImportError:
        npu_devices = list(Path("/dev").glob("davinci*"))
        return len(npu_devices) > 0


def get_default_paths() -> dict:
    project_root = get_project_root()
    model_root = Path("/models/AudioOperations/asr")
    return {
        'audio_list': project_root / "output_data" / "normalization" / "item.list",
        'result_dir': project_root / "output_data" / "asr",
        'wenet_wrapper': project_root / "src" / "utils" / "run_wenet.py",
        'aishell_model': model_root / "aishell" / "final.pt",
        'librispeech_model': model_root / "librispeech" / "final.pt",
    }


def resolve_device(device_arg: str) -> str:
    if device_arg == "auto":
        if check_npu_available():
            print_info("检测到 NPU 设备，使用 NPU")
            return "npu"
        else:
            print_info("未检测到 NPU 设备，使用 CPU")
            return "cpu"
    elif device_arg == "npu":
        if check_npu_available():
            return "npu"
        raise ValueError("指定使用 NPU，但设备不支持 NPU")
    elif device_arg == "cpu":
        return "cpu"
    raise ValueError(f"不支持的设备类型: {device_arg}")


def check_paths(paths: dict, language: str) -> None:
    if not paths['wenet_wrapper'].exists():
        raise FileNotFoundError(f"WeNet 包装器脚本不存在: {paths['wenet_wrapper']}")
    if not paths['audio_list'].exists():
        raise FileNotFoundError(f"音频列表文件不存在: {paths['audio_list']}")
    paths['result_dir'].mkdir(parents=True, exist_ok=True)
    if language == "zh":
        if not paths['aishell_model'].exists():
            raise FileNotFoundError(f"AIShell 模型文件不存在: {paths['aishell_model']}")
    elif language == "en":
        if not paths['librispeech_model'].exists():
            raise FileNotFoundError(f"LibriSpeech 模型文件不存在: {paths['librispeech_model']}")


def prepare_config(language: str) -> str:
    if language == "zh":
        model_dir = Path("/models/AudioOperations/asr/aishell")
    elif language == "en":
        model_dir = Path("/models/AudioOperations/asr/librispeech")
    else:
        raise ValueError(f"不支持的语言: {language}")
    yaml_files = list(model_dir.glob("*.yaml"))
    if not yaml_files:
        raise FileNotFoundError(f"在 {model_dir} 中未找到 YAML 配置文件")
    config_file = None
    for yaml_file in yaml_files:
        if yaml_file.name == "train.yaml":
            config_file = yaml_file
            break
    if config_file is None:
        config_file = yaml_files[0]
    return str(config_file)


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
    print_info("检查路径...")
    check_paths(paths, language)
    print_info("准备配置文件...")
    config_file = prepare_config(language)
    if language == "zh":
        model_file = str(paths['aishell_model'])
        model_name = "AIShell (中文)"
    elif language == "en":
        model_file = str(paths['librispeech_model'])
        model_name = "LibriSpeech (英文)"
    else:
        raise ValueError(f"不支持的语言: {language}")
    actual_device = resolve_device(device)
    cmd = [
        sys.executable,
        str(paths['wenet_wrapper']),
        "--mode", "ctc_greedy_search",
        "--device", actual_device,
        "--config", config_file,
        "--test_data", str(paths['audio_list']),
        "--checkpoint", model_file,
        "--batch_size", "1",
        "--result_dir", str(paths['result_dir']),
    ]
    print_header("语音识别配置")
    print_info(f"语言: {language} ({model_name})")
    print_info(f"设备: {actual_device}")
    print_info(f"音频列表: {paths['audio_list']}")
    print_info(f"结果目录: {paths['result_dir']}")
    print_info(f"配置文件: {Path(config_file).name}")
    print_info(f"模型文件: {Path(model_file).name}")
    try:
        with open(paths['audio_list'], 'r', encoding='utf-8') as f:
            audio_count = sum(1 for _ in f)
        print_info(f"音频数量: {audio_count}")
    except Exception as e:
        print_warning(f"无法统计音频数量: {e}")
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            bufsize=1,
            universal_newlines=True
        )
        output_queue = queue.Queue()
        stdout_thread = threading.Thread(target=read_output, args=(process.stdout, output_queue, 'stdout'))
        stderr_thread = threading.Thread(target=read_output, args=(process.stderr, output_queue, 'stderr'))
        stdout_thread.daemon = True
        stderr_thread.daemon = True
        stdout_thread.start()
        stderr_thread.start()
        while True:
            try:
                stream_name, line = output_queue.get(timeout=0.1)
                print(line)
            except queue.Empty:
                if process.poll() is not None:
                    try:
                        while True:
                            stream_name, line = output_queue.get_nowait()
                            print(line)
                    except queue.Empty:
                        pass
                    break
        return_code = process.wait()
        stdout_thread.join(timeout=1)
        stderr_thread.join(timeout=1)
        print("-" * 80)
        if return_code == 0:
            print_success("语音识别完成！")
            print_info(f"识别结果保存在: {paths['result_dir']}")
            result_files = list(paths['result_dir'].glob("*.txt"))
            if result_files:
                print_info("生成结果文件:")
                for result_file in result_files:
                    print_info(f"  - {result_file.name}")
            return 0
        else:
            print_error(f"识别失败，返回码: {return_code}")
            return return_code
    except subprocess.CalledProcessError as e:
        print_error(f"执行失败: {e}")
        if e.stderr:
            print_error(f"错误详情: {e.stderr}")
        return e.returncode
    except FileNotFoundError as e:
        print_error(f"文件不存在: {e}")
        return 1
    except Exception as e:
        print_error(f"未知错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


def create_wenet_wrapper(wrapper_path: Path):
    project_root = get_project_root()
    wrapper_content = '''#!/usr/bin/env python3
"""运行 WeNet 识别脚本的包装器"""
import sys
from pathlib import Path

def main():
    try:
        from wenet.bin.recognize import main as wenet_main
        wenet_main()
    except ImportError as e:
        print(f"[ERROR] 无法导入 WeNet 模块: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    wrapper_path.parent.mkdir(parents=True, exist_ok=True)
    with open(wrapper_path, 'w', encoding='utf-8') as f:
        f.write(wrapper_content)
    wrapper_path.chmod(0o755)
    print_info(f"已创建 WeNet 包装器脚本: {wrapper_path}")


def main():
    defaults = get_default_paths()
    parser = argparse.ArgumentParser(
        description="语音识别脚本 - 调用 WeNet 进行音频转文本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                               # 默认中文识别
  %(prog)s --language en                 # 英文识别
  %(prog)s --audio_list ./my_audio.list
  %(prog)s --result_dir ./my_results
  %(prog)s --device npu
        """
    )
    parser.add_argument("--language", "-l", choices=["zh", "en"], default="zh", help="音频语言")
    parser.add_argument("--audio_list", "-a", default=str(defaults['audio_list']), help="音频列表路径")
    parser.add_argument("--result_dir", "-r", default=str(defaults['result_dir']), help="结果目录")
    parser.add_argument("--device", "-d", choices=["auto", "npu", "cpu"], default="npu", help="设备")
    args = parser.parse_args()
    print_header("语音识别")
    try:
        import torch
        print_info(f"PyTorch 版本: {torch.__version__}")
    except ImportError:
        print_error("未安装 PyTorch，请先安装")
        return 1
    wenet_wrapper = defaults['wenet_wrapper']
    if not wenet_wrapper.exists():
        print_warning(f"WeNet 包装器不存在，尝试创建: {wenet_wrapper}")
        create_wenet_wrapper(wenet_wrapper)
    try:
        return run_recognize(
            language=args.language,
            audio_list=args.audio_list,
            result_dir=args.result_dir,
            device=args.device
        )
    except (ValueError, FileNotFoundError) as e:
        print_error(str(e))
        return 1
    except Exception as e:
        print_error(str(e))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
