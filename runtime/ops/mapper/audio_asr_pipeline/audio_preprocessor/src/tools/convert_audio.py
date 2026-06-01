#!/usr/bin/env python3
"""
音频转换工具
支持常见音频格式互转和属性调整（声道数、采样率、编码等）
使用本地pydub库，支持配置文件或命令行参数
"""

import argparse
import os
import sys
import shutil
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

# ==================== 相对路径导入 ====================

# 计算项目根目录
if __name__ == "__main__":
    CURRENT_DIR = Path(__file__).resolve().parent
else:
    CURRENT_DIR = Path.cwd()

# 项目根目录：向上两级到 audio_preprocessor
PROJECT_ROOT = CURRENT_DIR.parent.parent

# 导入颜色工具
COLOR_UTILS_PATH = PROJECT_ROOT / "src" / "utils" / "color_utils.py"
if COLOR_UTILS_PATH.exists():
    sys.path.insert(0, str(PROJECT_ROOT / "src" / "utils"))
    try:
        from color_utils import info, warning, error, ok, success, fail, header
    except ImportError as e:
        print(f"[WARNING] 无法导入颜色工具: {e}", file=sys.stderr)
        # 定义简单的替代函数
        def info(msg): return f"[INFO] {msg}"
        def warning(msg): return f"[WARNING] {msg}"
        def error(msg): return f"[ERROR] {msg}"
        def ok(msg): return f"[OK] {msg}"
        def success(msg): return f"[SUCCESS] {msg}"
        def fail(msg): return f"[FAIL] {msg}"
        def header(msg): return f"=== {msg} ==="
else:
    # 定义简单的替代函数
    def info(msg): return f"[INFO] {msg}"
    def warning(msg): return f"[WARNING] {msg}"
    def error(msg): return f"[ERROR] {msg}"
    def ok(msg): return f"[OK] {msg}"
    def success(msg): return f"[SUCCESS] {msg}"
    def fail(msg): return f"[FAIL] {msg}"
    def header(msg): return f"=== {msg} ==="

# ==================== 配置管理 ====================

class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        'audio_config': {
            'output_format': 'wav',
            'channels': 1,
            'sample_rate': 16000,
            'sample_width': 2,  # bytes
            'encoding': 'pcm_s16le',
            'bitrate': None,
            'input_format': ['mp3', 'wav', 'aac', 'm4a', 'flac', 'ogg', 'opus', 'wma'],
            'quality': 5,  # 1-9，仅某些格式有效
            'compression': None,  # 压缩级别
            'dither': None  # 抖动算法
        }
    }
    
    @staticmethod
    def find_config_file(config_path: Optional[str] = None) -> Path:
        """
        查找配置文件，按以下优先级：
        1. 命令行指定的路径
        2. 当前目录的 config/audio_config.yaml
        3. 项目根目录的 config/audio_config.yaml
        4. 用户主目录的 .audio_preprocessor/audio_config.yaml
        """
        if config_path:
            path = Path(config_path)
            if path.exists():
                return path
            else:
                raise FileNotFoundError(f"指定的配置文件不存在: {path}")
        
        search_paths = [
            Path.cwd() / "config" / "audio_config.yaml",
            PROJECT_ROOT / "config" / "audio_config.yaml",
            Path.home() / ".audio_preprocessor" / "audio_config.yaml",
        ]
        
        for path in search_paths:
            if path.exists():
                return path
        
        # 如果都找不到，返回默认路径
        return search_paths[1]  # 项目根目录的config
    
    @staticmethod
    def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件"""
        config_file = ConfigManager.find_config_file(config_path)
        
        if not config_file.exists():
            print(warning(f"配置文件不存在，使用默认配置"))
            return ConfigManager.DEFAULT_CONFIG.get('audio_config', {})
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 提取audio_config部分或使用顶级配置
            if 'audio_config' in config_data:
                config = config_data['audio_config']
            else:
                config = config_data
            
            # 确保必要的键存在
            default_config = ConfigManager.DEFAULT_CONFIG['audio_config']
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            
            print(info(f"已加载配置文件: {config_file}"))
            return config
            
        except yaml.YAMLError as e:
            print(error(f"配置文件格式错误: {e}"))
            print(warning("使用默认配置"))
            return ConfigManager.DEFAULT_CONFIG.get('audio_config', {})
        except Exception as e:
            print(error(f"加载配置文件失败: {e}"))
            print(warning("使用默认配置"))
            return ConfigManager.DEFAULT_CONFIG.get('audio_config', {})
    
    @staticmethod
    def merge_configs(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
        """合并配置文件和命令行参数"""
        merged = config.copy()
        
        # 映射命令行参数到配置键
        arg_mapping = {
            'output_format': 'format',
            'channels': 'channels',
            'sample_rate': 'sample_rate',
            'sample_width': 'sample_width',
            'encoding': 'encoding',
            'bitrate': 'bitrate',
            'quality': 'quality',
        }
        
        for config_key, arg_key in arg_mapping.items():
            arg_value = getattr(args, arg_key, None)
            if arg_value is not None:
                merged[config_key] = arg_value
        
        return merged

# ==================== 音频转换器 ====================

class AudioConverter:
    """音频转换器"""
    
    # 支持的输出格式和对应的编码器
    FORMAT_CODECS = {
        'wav': ['pcm_s16le', 'pcm_s24le', 'pcm_s32le', 'pcm_f32le', 'pcm_f64le'],
        'mp3': ['libmp3lame'],
        'flac': ['flac'],
        'ogg': ['libvorbis', 'opus'],
        'm4a': ['aac'],
        'aac': ['aac'],
        'opus': ['opus'],
        'wma': ['wmav2'],
        'aiff': ['pcm_s16be', 'pcm_s24be', 'pcm_s32be'],
    }
    
    # 格式到扩展名的映射
    FORMAT_EXTENSIONS = {
        'wav': '.wav',
        'mp3': '.mp3',
        'flac': '.flac',
        'ogg': '.ogg',
        'm4a': '.m4a',
        'aac': '.aac',
        'opus': '.opus',
        'wma': '.wma',
        'aiff': '.aiff',
    }
    
    def __init__(self):
        """初始化音频转换器"""
        self._import_pydub()
    
    def _import_pydub(self):
        """导入pydub库"""
        try:
            from pydub import AudioSegment
            self.AudioSegment = AudioSegment
            print(ok("成功导入 pydub 库"))
        except ImportError as e:
            print(error(f"无法导入 pydub: {e}"))
            print(info("请确保 pydub 已安装或本地库路径正确"))
            sys.exit(1)
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的输出格式"""
        return list(self.FORMAT_CODECS.keys())
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置，返回错误列表"""
        errors = []
        
        # 检查输出格式
        output_format = config.get('output_format', 'wav').lower()
        if output_format not in self.get_supported_formats():
            errors.append(f"不支持的输出格式: {output_format}")
        
        # 检查声道数
        channels = config.get('channels', 1)
        if channels not in [1, 2, 4, 6, 8]:
            errors.append(f"不支持的声道数: {channels} (支持: 1, 2, 4, 6, 8)")
        
        # 检查采样率
        sample_rate = config.get('sample_rate', 16000)
        if sample_rate <= 0:
            errors.append(f"无效的采样率: {sample_rate}")
        
        # 检查采样位宽
        sample_width = config.get('sample_width', 2)
        if sample_width not in [1, 2, 3, 4]:
            errors.append(f"不支持的采样位宽: {sample_width} (支持: 1, 2, 3, 4字节)")
        
        # 检查编码器
        encoding = config.get('encoding', '')
        if output_format in self.FORMAT_CODECS:
            supported_codecs = self.FORMAT_CODECS[output_format]
            if encoding and encoding not in supported_codecs:
                errors.append(f"格式 {output_format} 不支持的编码器: {encoding} (支持: {', '.join(supported_codecs)})")
        
        return errors
    
    def convert_audio(self, input_path: Path, output_path: Path, config: Dict[str, Any]) -> bool:
        """转换单个音频文件"""
        try:
            print(info(f"处理: {input_path.name}"))
            
            # 加载音频文件
            audio = self.AudioSegment.from_file(str(input_path))
            
            # 应用转换参数
            channels = config.get('channels', 1)
            if channels != audio.channels:
                audio = audio.set_channels(channels)
                print(info(f"  声道数: {audio.channels} -> {channels}"))
            
            sample_rate = config.get('sample_rate', 16000)
            if sample_rate != audio.frame_rate:
                audio = audio.set_frame_rate(sample_rate)
                print(info(f"  采样率: {audio.frame_rate} -> {sample_rate}"))
            
            sample_width = config.get('sample_width', 2)
            if sample_width != audio.sample_width:
                audio = audio.set_sample_width(sample_width)
                print(info(f"  采样位宽: {audio.sample_width} -> {sample_width}"))
            
            # 准备导出参数
            export_params = {}
            
            # 格式特定参数
            output_format = config.get('output_format', 'wav').lower()
            
            # 编码器
            encoding = config.get('encoding')
            if encoding:
                export_params['codec'] = encoding
            
            # 比特率
            bitrate = config.get('bitrate')
            if bitrate:
                export_params['bitrate'] = bitrate
            
            # 质量（某些格式使用）
            quality = config.get('quality')
            if quality is not None:
                if output_format in ['mp3', 'ogg', 'opus']:
                    export_params['quality'] = quality
            
            # 压缩级别
            compression = config.get('compression')
            if compression is not None:
                if output_format in ['flac']:
                    export_params['compression'] = compression
            
            # 导出音频
            audio.export(str(output_path), format=output_format, **export_params)
            
            # 验证输出文件
            if output_path.exists():
                output_size = output_path.stat().st_size / 1024  # KB
                print(ok(f"  转换成功: {output_path.name} ({output_size:.1f} KB)"))
                return True
            else:
                print(error(f"  转换失败: 输出文件未创建"))
                return False
                
        except Exception as e:
            print(error(f"  转换失败: {e}"))
            return False
    
    def batch_convert(self, input_files: List[Path], output_dir: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """批量转换音频文件"""
        results = {
            'total': len(input_files),
            'success': 0,
            'failed': 0,
            'failed_files': []
        }
        
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        
        print(header(f"开始批量转换 ({results['total']} 个文件)"))
        
        for i, input_file in enumerate(input_files, 1):
            print(info(f"[{i}/{results['total']}]"))
            
            # 确定输出文件名
            output_format = config.get('output_format', 'wav').lower()
            output_ext = self.FORMAT_EXTENSIONS.get(output_format, f".{output_format}")
            output_name = input_file.stem + output_ext
            output_path = output_dir / output_name
            
            # 执行转换
            if self.convert_audio(input_file, output_path, config):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['failed_files'].append(str(input_file))
        
        return results

# ==================== 命令行界面 ====================

def build_argparser() -> argparse.ArgumentParser:
    """构建命令行参数解析器"""
    
    # 获取支持的格式列表（动态）
    converter = AudioConverter()
    supported_formats = converter.get_supported_formats()
    
    parser = argparse.ArgumentParser(
        prog="convert_audio",
        description="音频转换工具 - 支持常见音频格式互转和属性调整",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s input.mp3 output.wav                    # 基本转换
  %(prog)s input.mp3 output.wav --sample-rate=44100 --channels=2
  %(prog)s *.mp3 output_dir/ --format=flac         # 批量转换
  %(prog)s input.wav output.mp3 --bitrate=192k     # 指定比特率
  %(prog)s --config=my_config.yaml input.wav output.flac
  
支持的输出格式: """ + ", ".join(supported_formats)
    )
    
    # 基本参数
    parser.add_argument(
        "input",
        nargs="+",
        help="输入音频文件或目录（支持通配符如 *.mp3）"
    )
    
    parser.add_argument(
        "output",
        help="输出文件或目录（如果是多个输入则必须是目录）"
    )
    
    # 配置文件
    parser.add_argument(
        "--config",
        default=None,
        help="自定义配置文件路径"
    )
    
    # 音频参数
    parser.add_argument(
        "--format",
        choices=supported_formats,
        help=f"输出格式（默认: wav）"
    )
    
    parser.add_argument(
        "--channels",
        type=int,
        choices=[1, 2, 4, 6, 8],
        help="声道数（默认: 1）"
    )
    
    parser.add_argument(
        "--sample-rate",
        type=int,
        help="采样率（Hz，默认: 16000）"
    )
    
    parser.add_argument(
        "--sample-width",
        type=int,
        choices=[1, 2, 3, 4],
        help="采样位宽（字节，默认: 2）"
    )
    
    parser.add_argument(
        "--encoding",
        help="编码器（格式相关，如 pcm_s16le, libmp3lame 等）"
    )
    
    parser.add_argument(
        "--bitrate",
        help="比特率（如 128k, 192k, 320k）"
    )
    
    parser.add_argument(
        "--quality",
        type=int,
        choices=range(0, 10),
        help="质量级别 0-9（仅某些格式有效）"
    )
    
    # 其他选项
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已存在的输出文件"
    )
    
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="列出支持的输出格式并退出"
    )
    
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="显示当前配置并退出"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="详细输出 (-v, -vv, -vvv)"
    )
    
    return parser

def expand_inputs(input_args: List[str]) -> List[Path]:
    """扩展输入参数（支持通配符）"""
    import glob
    
    input_files = []
    
    for arg in input_args:
        # 检查是否是通配符
        if '*' in arg or '?' in arg or '[' in arg:
            matches = glob.glob(arg, recursive=True)
            for match in matches:
                path = Path(match)
                if path.is_file():
                    input_files.append(path)
        else:
            path = Path(arg)
            if path.is_dir():
                # 目录：添加所有文件
                for file_path in path.rglob('*'):
                    if file_path.is_file():
                        input_files.append(file_path)
            elif path.is_file():
                input_files.append(path)
            else:
                print(warning(f"输入路径不存在: {arg}"))
    
    # 去重并排序
    input_files = sorted(set(input_files), key=lambda x: str(x))
    
    return input_files

def validate_input_files(input_files: List[Path], config: Dict[str, Any]) -> List[Path]:
    """验证输入文件"""
    if not input_files:
        print(error("未找到任何输入文件"))
        sys.exit(1)
    
    # 检查文件扩展名
    input_formats = config.get('input_format', [])
    allowed_exts = {f".{fmt.lower().lstrip('.')}" for fmt in input_formats}
    
    valid_files = []
    invalid_files = []
    
    for file_path in input_files:
        if file_path.suffix.lower() in allowed_exts:
            valid_files.append(file_path)
        else:
            invalid_files.append(file_path.name)
    
    if invalid_files:
        print(warning(f"跳过 {len(invalid_files)} 个不支持格式的文件"))
        if len(invalid_files) <= 10:  # 只显示前10个
            for file_name in invalid_files[:10]:
                print(f"  {file_name}")
            if len(invalid_files) > 10:
                print(f"  ... 还有 {len(invalid_files) - 10} 个")
    
    return valid_files

def main():
    """主函数"""
    # 解析命令行参数
    parser = build_argparser()
    args = parser.parse_args()
    
    # 显示标题
    print(header("音频转换工具"))
    
    # 列出支持的格式
    if args.list_formats:
        converter = AudioConverter()
        print(info("支持的输出格式:"))
        for fmt in converter.get_supported_formats():
            codecs = converter.FORMAT_CODECS.get(fmt, [])
            if codecs:
                print(f"  {fmt}: {', '.join(codecs)}")
            else:
                print(f"  {fmt}")
        sys.exit(0)
    
    # 加载配置
    config = ConfigManager.load_config(args.config)
    
    # 显示配置
    if args.show_config:
        print(header("当前配置"))
        for key, value in config.items():
            if isinstance(value, list):
                print(f"  {key}: {', '.join(map(str, value))}")
            else:
                print(f"  {key}: {value}")
        sys.exit(0)
    
    # 合并命令行参数到配置
    config = ConfigManager.merge_configs(config, args)
    
    # 验证配置
    converter = AudioConverter()
    errors = converter.validate_config(config)
    if errors:
        print(error("配置错误:"))
        for err in errors:
            print(f"  {err}")
        sys.exit(1)
    
    # 扩展输入文件
    input_files = expand_inputs(args.input)
    
    # 验证输入文件
    valid_files = validate_input_files(input_files, config)
    
    if not valid_files:
        print(error("没有有效的输入文件"))
        sys.exit(1)
    
    print(info(f"找到 {len(valid_files)} 个音频文件"))
    
    # 检查ffmpeg/avconv
    if shutil.which("ffmpeg") is None and shutil.which("avconv") is None:
        print(warning("未检测到 ffmpeg/avconv，部分格式可能无法处理"))
    
    # 确定输出路径
    output_path = Path(args.output)
    
    # 单个文件输出
    if len(valid_files) == 1:
        input_file = valid_files[0]
        
        # 如果输出是目录
        if output_path.exists() and output_path.is_dir():
            output_format = config.get('output_format', 'wav').lower()
            output_ext = converter.FORMAT_EXTENSIONS.get(output_format, f".{output_format}")
            output_file = output_path / (input_file.stem + output_ext)
        else:
            output_file = output_path
        
        # 检查文件是否存在
        if output_file.exists() and not args.overwrite:
            response = input(f"输出文件已存在: {output_file.name}，是否覆盖？ (y/n): ").lower()
            if response not in ['y', 'yes']:
                print(info("用户取消操作"))
                sys.exit(0)
        
        # 创建输出目录
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 执行转换
        success = converter.convert_audio(input_file, output_file, config)
        
        if success:
            print(success("转换完成"))
            sys.exit(0)
        else:
            print(fail("转换失败"))
            sys.exit(1)
    
    # 批量转换
    else:
        # 输出必须是目录
        if output_path.exists() and output_path.is_file():
            print(error("多个输入文件时，输出必须为目录"))
            sys.exit(1)
        
        # 检查目录中是否已有文件
        if output_path.exists():
            existing_files = list(output_path.glob("*"))
            if existing_files and not args.overwrite:
                response = input(f"输出目录已有 {len(existing_files)} 个文件，是否继续？ (y/n): ").lower()
                if response not in ['y', 'yes']:
                    print(info("用户取消操作"))
                    sys.exit(0)
        
        # 执行批量转换
        results = converter.batch_convert(valid_files, output_path, config)
        
        # 显示结果
        print(header("转换结果"))
        print(info(f"总计: {results['total']} 个文件"))
        print(ok(f"成功: {results['success']} 个"))
        
        if results['failed'] > 0:
            print(error(f"失败: {results['failed']} 个"))
            if results['failed_files'] and args.verbose > 0:
                print(info("失败的文件:"))
                for file_path in results['failed_files'][:10]:  # 最多显示10个
                    print(f"  {Path(file_path).name}")
                if len(results['failed_files']) > 10:
                    print(f"  ... 还有 {len(results['failed_files']) - 10} 个")
        
        if results['success'] == results['total']:
            print(success("所有文件转换成功！"))
        elif results['success'] > 0:
            print(info("部分文件转换完成"))
        else:
            print(fail("所有文件转换失败"))
        
        sys.exit(0 if results['success'] > 0 else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + info("用户中断操作"))
        sys.exit(130)
    except Exception as e:
        print(error(f"程序错误: {e}"))
        if __debug__:  # 调试模式下显示详细错误
            import traceback
            traceback.print_exc()
        sys.exit(1)
