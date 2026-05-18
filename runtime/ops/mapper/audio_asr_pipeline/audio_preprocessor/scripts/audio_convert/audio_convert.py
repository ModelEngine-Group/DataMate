#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence, Optional

# 导入配置加载模块和颜色工具
try:
    from config_loader import get_audio_config, clear_config_cache
    from color_utils import info, warning, error, ok, header, success, fail
except ImportError:
    # 如果模块导入失败，尝试从当前目录导入
    sys.path.insert(0, str(Path(__file__).parent))
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "utils"))

    try:
        from config_loader import get_audio_config, clear_config_cache
        from color_utils import info, warning, error, ok, header, success, fail
    except ImportError as e:
        print(f"[ERROR] 无法导入 config_loader: {e}", file=sys.stderr)
        sys.exit(1)


def get_allowed_input_exts(config_path: Optional[str] = None) -> set[str]:
    """从配置文件获取允许的输入扩展名
    
    Args:
        config_path: 配置文件路径，可选
        
    Returns:
        set[str]: 允许的扩展名集合
    """
    config = get_audio_config(config_path)
    input_formats = config.get('input_format', ['mp3', 'wav', 'aac', 'm4a', 'flac'])
    return {f".{fmt.lower().lstrip('.')}" for fmt in input_formats}


@dataclass(frozen=True)
class ConvertSpec:
    """音频转换规格，从配置文件初始化"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化转换规格
        
        Args:
            config_path: 配置文件路径，可选
        """
        # 从配置获取默认值
        config = get_audio_config(config_path)
        
        # 使用field无法直接传递参数，我们通过__post_init__设置
        object.__setattr__(self, 'channels', config.get('channels', 1))
        object.__setattr__(self, 'frame_rate', config.get('sample_rate', 16000))
        object.__setattr__(self, 'sample_width_bytes', config.get('sample_width', 2))
        object.__setattr__(self, 'encoding', config.get('encoding', 'pcm_s16le'))
        object.__setattr__(self, 'output_format', config.get('output_format', 'wav'))
        
        self.__post_init__()
    
    # 这些属性将在__init__中设置
    channels: int
    frame_rate: int
    sample_width_bytes: int
    encoding: str
    output_format: str
    
    def __post_init__(self):
        """验证配置值"""
        if self.channels not in [1, 2]:
            raise ValueError(f"声道数必须是1或2，当前: {self.channels}")
        if self.frame_rate <= 0:
            raise ValueError(f"采样率必须为正数，当前: {self.frame_rate}")
        if self.sample_width_bytes not in [1, 2, 3, 4]:
            raise ValueError(f"采样位宽必须是1-4字节，当前: {self.sample_width_bytes}")


def _repo_root() -> Path:
    # audio_preprocessor/audio_convert/cli.py -> audio_preprocessor/
    return Path(__file__).resolve().parents[1]


def _import_local_pydub():
    """
    Prefer the repo-local pydub clone at audio_preprocessor/pydub over any site-packages install.
    """
    root = _repo_root()
    local_pydub = root.parent / "local_libs" / "pydub"
    if local_pydub.is_dir():
        sys.path.insert(0, str(local_pydub))
    try:
        from pydub import AudioSegment  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "无法导入 pydub。请确认本地目录存在："
            f"{local_pydub}，或已安装 pydub。原始错误：{e}"
        ) from e
    return AudioSegment


def _read_index_file(path: Path) -> List[Path]:
    if not path.exists():
        raise FileNotFoundError(f"索引文件不存在: {path}")
    items: List[Path] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        items.append(Path(s))
    return items


def _expand_inputs(paths: Sequence[str], index_file: str | None) -> List[Path]:
    inputs: List[Path] = []
    if index_file:
        inputs.extend(_read_index_file(Path(index_file)))
    inputs.extend(Path(p) for p in paths)
    # de-dup while preserving order
    seen = set()
    uniq: List[Path] = []
    for p in inputs:
        key = os.fspath(p)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(p)
    return uniq


def _validate_inputs(inputs: Sequence[Path], config_path: Optional[str] = None) -> None:
    """验证输入文件，使用配置中的允许格式
    
    Args:
        inputs: 输入文件路径序列
        config_path: 配置文件路径，可选
    """
    if not inputs:
        raise ValueError("未提供输入音频路径。请使用位置参数或 --index_file。")
    
    allowed_exts = get_allowed_input_exts(config_path)
    
    for p in inputs:
        if not p.exists():
            raise FileNotFoundError(f"输入文件不存在: {p}")
        if not p.is_file():
            raise ValueError(f"输入不是文件: {p}")
        ext = p.suffix.lower()
        if ext not in allowed_exts:
            raise ValueError(
                f"不支持的源音频格式: {p}（{ext}）。仅支持: "
                + ", ".join(sorted(x.lstrip('.') for x in allowed_exts))
            )


def _resolve_output_paths(inputs: Sequence[Path], output: Path, config_path: Optional[str] = None) -> List[Path]:
    """
    解析输出路径，使用配置中的输出格式
    
    Args:
        inputs: 输入文件路径序列
        output: 输出路径
        config_path: 配置文件路径，可选
        
    Returns:
        List[Path]: 输出文件路径列表
    """
    config = get_audio_config(config_path)
    output_ext = f".{config.get('output_format', 'wav').lower().lstrip('.')}"
    
    if len(inputs) == 1:
        src = inputs[0]
        # If output exists and is a directory, treat as directory output.
        if output.exists() and output.is_dir():
            return [output / f"{src.stem}{output_ext}"]
        # If user explicitly ends with path separator, treat as directory output.
        if str(output).endswith(os.sep):
            return [output / f"{src.stem}{output_ext}"]
        # File output: check extension
        if output.suffix == "":
            return [output.with_suffix(output_ext)]
        if output.suffix.lower() != output_ext:
            raise ValueError(f"输出文件必须是 {output_ext} 后缀（或不给后缀让工具自动补{output_ext}）。")
        return [output]

    # multiple inputs
    out_dir = output
    if output.exists() and output.is_file():
        raise ValueError("多输入模式下，--output 必须是目录路径，不能是文件路径。")
    return [out_dir / f"{src.stem}{output_ext}" for src in inputs]


def _ensure_parent_dirs(paths: Iterable[Path]) -> None:
    for p in paths:
        p.parent.mkdir(parents=True, exist_ok=True)


def _check_ffmpeg_hint() -> str | None:
    # pydub relies on ffmpeg/avlib. Give a clear hint if missing.
    if shutil.which("ffmpeg") is None and shutil.which("avconv") is None:
        return "未检测到 ffmpeg/avconv，pydub 可能无法解码 mp3/aac/m4a/flac。请先安装 ffmpeg。"
    return None


def convert_one(AudioSegment, src: Path, dst: Path, spec: ConvertSpec) -> bool:
    """转换单个音频文件，使用配置中的规格
    
    Args:
        AudioSegment: pydub 的 AudioSegment 类
        src: 源文件路径
        dst: 目标文件路径
        spec: 转换规格
        
    Returns:
        bool: 转换是否成功
    """
    try:
        audio = AudioSegment.from_file(src)
        audio = audio.set_channels(spec.channels)
        audio = audio.set_frame_rate(spec.frame_rate)
        audio = audio.set_sample_width(spec.sample_width_bytes)
        # 使用配置中的编码格式导出
        audio.export(dst, format=spec.output_format, codec=spec.encoding)
        return True
    except Exception as e:
        print(error(f"转换失败 {src.name}: {e}"))
        return False


def build_argparser() -> argparse.ArgumentParser:
    """构建命令行参数解析器"""
    # 使用默认配置显示帮助信息
    config = get_audio_config()
    output_format = config.get('output_format', 'wav')
    
    p = argparse.ArgumentParser(
        prog="audio_convert",
        description=(
            f"将音频统一转换为 {output_format.upper()}："
            f"{config.get('channels', 1)}通道 / "
            f"{config.get('sample_rate', 16000)}Hz / "
            f"{config.get('sample_width', 2)*8}bit {config.get('encoding', 'pcm_s16le')}。\n"
            f"支持源格式: {', '.join(config.get('input_format', []))}"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument(
        "inputs",
        nargs="*",
        help="输入音频路径：可传 1 个或多个文件路径",
    )
    p.add_argument(
        "--index_file",
        "-f",
        default=None,
        help="索引文件路径：文件中每行一个音频路径（支持 # 注释与空行）",
    )
    p.add_argument(
        "--output",
        "-o",
        required=True,
        help=(
            "输出路径：\n"
            f"- 单输入：可为文件或目录（自动添加 .{output_format} 后缀）\n"
            "- 多输入：必须为目录\n"
        ),
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="允许覆盖已存在的输出文件",
    )
    p.add_argument(
        "--config",
        "-c",
        default=None,
        help="自定义配置文件路径，不指定则使用默认配置",
    )
    p.add_argument(
        "--show_config",
        action="store_true",
        help="显示当前配置并退出",
    )
    return p


def print_config_info(config_path: Optional[str] = None) -> None:
    """打印当前配置信息
    
    Args:
        config_path: 配置文件路径，可选
    """
    config = get_audio_config(config_path)
    print(header("当前音频转换配置"))
    if config_path:
        print(info(f"配置文件: {config_path}"))
    else:
        print(info("配置文件: 使用默认配置"))
    print(info(f"输出格式: {config.get('output_format')}"))
    print(info(f"声道数: {config.get('channels')}"))
    print(info(f"采样率: {config.get('sample_rate')} Hz"))
    print(info(f"采样位宽: {config.get('sample_width')} 字节 ({config.get('sample_width')*8} bit)"))
    print(info(f"编码格式: {config.get('encoding')}"))
    print(info(f"输入格式: {', '.join(config.get('input_format', []))}"))
    
    # 如果有质量检查配置，也显示
    if 'quality_checks' in config:
        print(info("质量检查:"))
        qc = config['quality_checks']
        print(f"  - 最小时长: {qc.get('min_duration_seconds')}秒")
        print(f"  - 最大时长: {qc.get('max_duration_seconds')}秒")
        print(f"  - 最大静音比例: {qc.get('max_silence_ratio')}")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argparser().parse_args(argv)
    
    # 如果指定了配置文件，清除缓存并重新加载配置
    if args.config:
        clear_config_cache()
    
    # 显示配置信息
    if args.show_config:
        print_config_info(args.config)
        return 0
    
    # 注意：这里需要在解析参数后获取配置，因为用户可能指定了--config
    inputs = _expand_inputs(args.inputs, args.index_file)
    _validate_inputs(inputs, args.config)

    ffmpeg_hint = _check_ffmpeg_hint()
    if ffmpeg_hint:
        print(warning(ffmpeg_hint))

    out = Path(args.output)
    out_paths = _resolve_output_paths(inputs, out, args.config)
    _ensure_parent_dirs(out_paths)

    if not args.overwrite:
        exists = [p for p in out_paths if p.exists()]
        if exists:
            print(warning(f"检测到 {len(exists)} 个输出文件已存在"))
            response = input("是否覆盖这些文件？(y/n, 回车确认 y): ").strip().lower()
            if response not in ['y', 'yes', '']:
                print(info("用户取消操作，程序结束"))
                return 0

    AudioSegment = _import_local_pydub()
    spec = ConvertSpec(args.config)
    
    success_count = 0
    total_count = len(inputs)

    for src, dst in zip(inputs, out_paths):
        if convert_one(AudioSegment, src=src, dst=dst, spec=spec):
            # 只输出文件名
            print(ok(f"转换成功: {src.name}"))
            success_count += 1
        else:
            print(error(f"转换失败: {src.name}"))

    # 显示统计信息
    if success_count == total_count:
        print(success(f"所有 {total_count} 个文件转换完成"))
    else:
        print(warning(f"转换完成: {success_count}/{total_count} 个文件成功"))
        if success_count < total_count:
            print(error(f"{total_count - success_count} 个文件转换失败"))

    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    raise SystemExit(main())