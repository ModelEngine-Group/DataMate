#!/usr/bin/env python3
"""
生成音频文件索引表工具
将指定文件夹中的wav文件枚举为JSON格式的索引表
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

# 添加脚本所在目录到系统路径，导入颜色工具
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "audio_convert"))
    from color_utils import info, warning, error, ok, success, header
except ImportError:
    # 如果无法导入颜色工具，使用普通打印
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
    
    # 创建包装函数，使其行为与颜色版本相同
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
    # 如果成功导入，创建打印包装函数
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


def get_default_audio_dir() -> Path:
    """
    获取默认音频文件夹路径
    
    Returns:
        Path: 默认音频文件夹路径
    """
    # 根据项目结构，音频预处理器的output_data/normalization目录
    project_root = Path(__file__).parent.parent.parent
    return project_root / "output_data" / "normalization"


def find_wav_files(audio_dir: Path) -> List[Path]:
    """
    查找音频文件夹中的所有.wav文件
    
    Args:
        audio_dir: 音频文件夹路径
        
    Returns:
        List[Path]: .wav文件路径列表
    """
    if not audio_dir.exists():
        print_error(f"音频文件夹不存在: {audio_dir}")
        return []
    
    # 查找所有.wav文件（包括子目录）
    wav_files = []
    for pattern in ["*.wav", "*.WAV"]:
        wav_files.extend(list(audio_dir.rglob(pattern)))
    
    return sorted(wav_files)


def generate_item_list(audio_dir: Path, output_file: Path, key_prefix: Optional[str] = None) -> int:
    """
    生成音频索引表
    
    Args:
        audio_dir: 音频文件夹路径
        output_file: 输出文件路径
        key_prefix: 键值前缀，可选
        
    Returns:
        int: 生成的文件数量
    """
    # 查找wav文件
    print_info(f"扫描音频文件夹: {audio_dir}")
    wav_files = find_wav_files(audio_dir)
    
    if not wav_files:
        print_warning("未找到任何.wav文件")
        return 0
    
    print_info(f"找到 {len(wav_files)} 个.wav文件")
    
    # 确保输出文件的父目录存在
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 生成索引表
    items = []
    for idx, wav_file in enumerate(wav_files):
        # 生成键值
        if key_prefix:
            key = f"{key_prefix}{idx}"
        else:
            key = wav_file.stem  # 使用文件名（不带扩展名）
        
        # 构建绝对路径
        wav_abs_path = wav_file.resolve()
        
        # 创建项目字典
        item = {
            "key": key,
            "wav": str(wav_abs_path),
            "txt": ""
        }
        
        items.append(item)
    
    # 写入文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in items:
                json_line = json.dumps(item, ensure_ascii=False)
                f.write(json_line + "\n")
        
        print_ok(f"已生成索引表: {output_file}")
        print_info(f"共写入 {len(items)} 条记录")
        
        
        return len(items)
        
    except Exception as e:
        print_error(f"写入文件失败: {e}")
        return 0


def parse_arguments():
    """解析命令行参数"""
    # 获取默认音频文件夹
    default_audio_dir = get_default_audio_dir()
    
    parser = argparse.ArgumentParser(
        description="生成音频文件索引表工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                           # 使用默认配置
  %(prog)s --audio_dir ./my_audio --output ./my_list.txt
  %(prog)s --audio_dir ./audio --key_prefix sample_
  %(prog)s --audio_dir ./wavs --output ./index.jsonl --key_prefix audio_
        """
    )
    
    parser.add_argument(
        "--audio_dir",
        "-a",
        default=str(default_audio_dir),
        help=f"音频文件夹路径，默认: {default_audio_dir}"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="输出列表文件路径，默认: {音频文件夹}/item.list"
    )
    
    parser.add_argument(
        "--key_prefix",
        "-k",
        default=None,
        help="键值前缀，例如 'audio_' 会生成 'audio_0', 'audio_1', ..."
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    
    print_header("生成音频索引")
    
    # 解析音频文件夹路径（支持相对路径）
    audio_dir = Path(args.audio_dir).resolve()
    if not audio_dir.exists():
        print_error(f"指定的音频文件夹不存在: {audio_dir}")
        print_info("请确保路径正确或先运行音频归一化处理")
        return 1
    
    print_info(f"音频文件夹: {audio_dir}")
    
    # 确定输出文件路径
    if args.output:
        output_file = Path(args.output).resolve()
    else:
        output_file = audio_dir / "item.list"
    
    print_info(f"输出文件: {output_file}")
    
    # 如果指定了键值前缀
    
    # 查找wav文件
    wav_files = find_wav_files(audio_dir)
    
    if not wav_files:
        print_warning("未找到任何.wav文件，程序退出")
        return 0
        
    # 生成索引表
    print_info("开始生成索引表...")
    item_count = generate_item_list(audio_dir, output_file, args.key_prefix)
    
    if item_count > 0:
        print_success(f"索引表生成完成！共生成 {item_count} 条记录")
        print_info(f"文件保存在: {output_file}")
    else:
        print_warning("索引表生成失败或未生成任何记录")
    
    return 0 if item_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())