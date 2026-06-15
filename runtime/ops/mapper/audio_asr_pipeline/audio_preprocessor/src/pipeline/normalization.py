#!/usr/bin/env python3
"""
音频归一化处理脚本
自动扫描输入文件夹，调用 audio_convert 进行批量转换
提供默认的输入/输出文件夹，支持自定义配置
"""
import argparse
import sys
import os
from pathlib import Path
from typing import List, Optional, Tuple
import subprocess

# 添加脚本所在目录到系统路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "audio_convert"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "utils"))

# 导入 config_loader 模块和颜色工具
try:
    from config_loader import get_audio_config, clear_config_cache, create_default_config, find_config_file
    from color_utils import info, warning, error, ok, header, success, fail, question
except ImportError as e:
    print(f"[ERROR] 无法导入模块: {e}", file=sys.stderr)
    print(f"[INFO] 当前搜索路径: {sys.path}")
    sys.exit(1)

print(header("音频标准化处理"))

def get_default_directories() -> tuple[Path, Path]:
    """
    获取默认的输入和输出目录
    
    Returns:
        tuple[Path, Path]: (input_dir, output_dir)
    """
    # 当前工作目录下的默认目录
    current_dir = Path.cwd()
    input_dir = current_dir.parent.parent / "input_data" / "audio_raw"
    output_dir = current_dir.parent.parent / "output_data" / "normalization"
    
    return input_dir, output_dir


def scan_input_directory(input_dir: Path, config_path: Optional[str] = None) -> Tuple[List[str], List[str], int]:
    """
    扫描输入目录中的文件，返回音频文件、其他文件列表和其他文件数量
    
    Args:
        input_dir: 输入目录
        config_path: 配置文件路径，用于获取支持的格式
        
    Returns:
        Tuple[List[str], List[str], int]: (音频文件列表, 其他文件列表, 其他文件数量)
    """
    # 获取支持的格式
    config = get_audio_config(config_path)
    input_formats = config.get('input_format', ['mp3', 'wav', 'aac', 'm4a', 'flac'])
    
    # 构建扩展名集合
    extensions = {f".{fmt.lower().lstrip('.')}" for fmt in input_formats}
    
    # 查找文件
    audio_files = []
    other_files = []
    
    # 使用 rglob 扫描所有文件
    for item in input_dir.rglob("*"):
        if item.is_file():
            if item.suffix.lower() in extensions:
                audio_files.append(str(item))
            else:
                other_files.append(str(item))
    
    return audio_files, other_files, len(other_files)


def find_audio_files(input_dir: Path, config_path: Optional[str] = None) -> List[str]:
    """
    查找输入目录中的音频文件
    
    Args:
        input_dir: 输入目录
        config_path: 配置文件路径，用于获取支持的格式
        
    Returns:
        List[str]: 音频文件路径列表
    """
    audio_files, _, _ = scan_input_directory(input_dir, config_path)
    return sorted(set(audio_files))


def check_existing_output_files(audio_files: List[str], output_dir: Path, 
                               config_path: Optional[str] = None) -> List[str]:
    """
    检查输出目录中已存在的文件
    
    Args:
        audio_files: 音频文件列表
        output_dir: 输出目录
        config_path: 配置文件路径
        
    Returns:
        List[str]: 已存在的输出文件列表
    """
    config = get_audio_config(config_path)
    output_ext = f".{config.get('output_format', 'wav').lower().lstrip('.')}"
    
    existing_files = []
    for audio_file in audio_files:
        src = Path(audio_file)
        dst = output_dir / f"{src.stem}{output_ext}"
        if dst.exists():
            existing_files.append(str(dst))
    
    return existing_files


def ask_user_confirmation(prompt: str) -> bool:
    """
    询问用户确认
    
    Args:
        prompt: 提示信息
        
    Returns:
        bool: 用户是否确认
    """
    response = input(f"{question(prompt)} ([y]/n): ").strip().lower()
    return response in ['y', 'yes', '']


def run_audio_convert(input_files: List[str], output_dir: Path, 
                     config_path: Optional[str] = None, overwrite: bool = False) -> int:
    """
    调用 audio_convert.py 进行转换
    
    Args:
        input_files: 输入文件列表
        output_dir: 输出目录
        config_path: 配置文件路径
        overwrite: 是否覆盖已存在文件
        
    Returns:
        int: 返回码
    """
    if not input_files:
        print(warning("未找到任何音频文件，跳过转换"))
        return 0
    
    # 获取 audio_convert.py 的绝对路径
    audio_convert_path = Path(__file__).parent.parent.parent / "scripts" / "audio_convert" / "audio_convert.py"
    
    if not audio_convert_path.exists():
        print(error(f"audio_convert.py 未找到: {audio_convert_path}"))
        return 1
    
    # 构建命令行参数
    cmd = [sys.executable, str(audio_convert_path)]
    
    # 添加输入文件
    cmd.extend(input_files)
    
    # 添加输出目录
    cmd.extend(["--output", str(output_dir)])
    
    # 添加配置文件（如果指定）
    if config_path:
        cmd.extend(["--config", config_path])
    
    # 添加覆盖选项
    if overwrite:
        cmd.append("--overwrite")
    
    # 显示配置文件信息
    config_file = find_config_file(config_path)
    print(info(f"使用配置文件: {config_file}"))
    
    # 显示处理的文件数量
    print(info(f"准备处理 {len(input_files)} 个音频文件"))
    
    # 显示音频文件名（仅文件名）
    print(info("音频文件列表:"))
    for audio_file in input_files:
        file_name = Path(audio_file).name
        print(f"  - {file_name}")
    
    # 执行命令
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        
        # 解析输出，提取成功信息
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            success_count = 0
            for line in lines:
                if "[OK]" in line:
                    # 提取文件名
                    parts = line.split(" -> ")
                    if len(parts) == 2:
                        src_path = Path(parts[0].replace("[OK] ", "").strip())
                        dst_path = Path(parts[1].strip())
                        file_name = src_path.name
                        print(ok(f"转换成功: {file_name}"))
                        success_count += 1
        
        if result.stderr:
            print(error(f"错误输出: {result.stderr}"))
        
        return result.returncode
        
    except subprocess.CalledProcessError as e:
        print(error(f"转换失败: {e}"))
        print(error(f"错误输出: {e.stderr}"))
        return e.returncode


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="音频归一化处理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                           # 使用默认配置和目录
  %(prog)s --input_dir my_input --output_dir my_output
  %(prog)s --config my_config.yaml --overwrite
  %(prog)s --input_dir /path/to/input --config custom_config.yaml
        """
    )
    
    # 获取默认目录
    default_input_dir, default_output_dir = get_default_directories()
    
    parser.add_argument(
        "--input_dir",
        "-i",
        default=str(default_input_dir),
        help=f"输入音频文件夹路径，默认: {default_input_dir}"
    )
    
    parser.add_argument(
        "--output_dir",
        "-o",
        default=str(default_output_dir),
        help=f"输出音频文件夹路径，默认: {default_output_dir}"
    )
    
    parser.add_argument(
        "--config",
        "-c",
        default=None,
        help="自定义配置文件路径，不指定则使用默认配置"
    )
    
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已存在的输出文件"
    )
    
    parser.add_argument(
        "--show_config",
        action="store_true",
        help="显示配置信息并退出"
    )
    
    parser.add_argument(
        "--create_default_config",
        action="store_true",
        help="创建默认配置文件并退出"
    )
    
    args = parser.parse_args()
    
    # 创建默认配置文件
    if args.create_default_config:
        config_path = find_config_file(args.config)
        create_default_config(config_path)
        print(info(f"已创建默认配置文件: {config_path}"))
        return 0
    
    # 显示配置信息
    if args.show_config:
        # 运行 audio_convert 的 show_config 选项
        audio_convert_path = Path(__file__).parent.parent.parent / "scripts" / "audio_convert" / "audio_convert.py"
        cmd = [sys.executable, str(audio_convert_path), "--show_config"]
        if args.config:
            cmd.extend(["--config", args.config])
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(error(f"获取配置失败: {e}"))
            print(error(f"错误输出: {e.stderr}"))
        return 0
    
    # 确保目录存在
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    if not input_dir.exists():
        print(error(f"输入目录不存在: {input_dir}"))
        print(info(f"请创建目录: mkdir -p {input_dir}"))
        return 1
    
    if not output_dir.exists():
        print(info(f"输出目录不存在，自动创建: {output_dir}"))
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # 查找音频文件和其他文件
    print(info(f"扫描输入目录: {input_dir}"))
    audio_files, other_files, other_count = scan_input_directory(input_dir, args.config)
    
    if not audio_files:
        print(warning(f"在 {input_dir} 中未找到任何支持的音频文件"))
        print(info(f"支持的格式: mp3, wav, aac, m4a, flac (可在配置文件中修改)"))
        return 0
    
    print(info(f"找到 {len(audio_files)} 个音频文件"))
    if other_count > 0:
        print(info(f"找到 {other_count} 个其他文件（非音频格式）"))
    
    # 检查是否需要覆盖
    existing_files = check_existing_output_files(audio_files, output_dir, args.config)
    need_overwrite = False
    
    if existing_files and not args.overwrite:
        print(warning(f"检测到 {len(existing_files)} 个输出文件已存在"))
        if ask_user_confirmation("是否覆盖这些文件？"):
            need_overwrite = True
        else:
            print(info("用户取消操作，程序结束"))
            return 0
    elif args.overwrite and existing_files:
        print(info(f"已启用覆盖模式，将覆盖 {len(existing_files)} 个已存在文件"))
        need_overwrite = True
    
    # 运行转换
    return_code = run_audio_convert(audio_files, output_dir, args.config, need_overwrite or args.overwrite)
    
    # 显示完成提示
    if return_code == 0:
        print(success(f"音频归一化处理完成！共处理 {len(audio_files)} 个文件"))
    else:
        print(fail(f"音频归一化处理失败，错误码: {return_code}"))
    
    return return_code


if __name__ == "__main__":
    sys.exit(main())