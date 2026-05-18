#!/usr/bin/env python3
"""
轻量 YAML 配置加载器（面向 argparse 脚本）。

目标：
- 允许脚本通过 --config xxx.yaml 读取配置
- YAML 中与 argparse dest 同名的键会作为“默认值”
- 命令行显式传入的参数优先级更高（覆盖配置）
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def _safe_import_yaml():
    try:
        import yaml  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "缺少 PyYAML 依赖，无法读取 YAML 配置文件。请安装 pyyaml。"
        ) from e
    return yaml


def load_yaml_dict(path: Path) -> Dict[str, Any]:
    yaml = _safe_import_yaml()
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML 顶层必须是 dict，实际是: {type(data)}")
    return data


def pick_section(config: Dict[str, Any], section: Optional[str]) -> Dict[str, Any]:
    """
    支持三种写法：
    1) 顶层就是参数 dict
    2) 顶层包含 {section: {...}}
    3) 顶层只有一个 key 且 value 是 dict（例如 audio_config.yaml 里的 audio_config）
    """
    if not config:
        return {}

    if section and isinstance(config.get(section), dict):
        return dict(config[section])

    if len(config) == 1:
        only_val = next(iter(config.values()))
        if isinstance(only_val, dict):
            return dict(only_val)

    return dict(config)


def _parser_dests(parser: argparse.ArgumentParser) -> set[str]:
    dests: set[str] = set()
    for a in parser._actions:  # noqa: SLF001 - argparse 内部字段，足够稳定
        if getattr(a, "dest", None):
            dests.add(a.dest)
    return dests


def apply_yaml_defaults_to_parser(
    parser: argparse.ArgumentParser,
    cfg: Dict[str, Any],
) -> None:
    dests = _parser_dests(parser)
    defaults: Dict[str, Any] = {k: v for k, v in cfg.items() if k in dests}
    if defaults:
        parser.set_defaults(**defaults)


def parse_args_with_yaml_config(
    parser: argparse.ArgumentParser,
    *,
    section: Optional[str] = None,
    config_dest: str = "config",
    default_config_paths: Optional[Iterable[Path]] = None,
    auto_use_default_config_when_no_args: bool = True,
) -> argparse.Namespace:
    """
    两阶段解析：
    - 先仅解析 --config 得到 YAML 路径
    - 读取 YAML 并把同名键写入 parser defaults
    - 再做完整 parse_args，保证 CLI 覆盖 YAML
    """
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--config", "-c", default=None, dest=config_dest)
    pre_ns, _ = pre.parse_known_args()

    cfg_path = getattr(pre_ns, config_dest, None)
    cfg_file: Optional[Path] = None
    if cfg_path:
        cfg_file = Path(str(cfg_path)).expanduser().resolve()
        if not cfg_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {cfg_file}")
    else:
        # 当用户没有指定任何参数时（仅脚本名），尝试在默认路径查找配置文件
        no_user_args = len(sys.argv) <= 1
        if auto_use_default_config_when_no_args and no_user_args and default_config_paths:
            for p in default_config_paths:
                pp = Path(p).expanduser().resolve()
                if pp.exists():
                    cfg_file = pp
                    break

    if cfg_file and cfg_file.exists():
        cfg_root = load_yaml_dict(cfg_file)
        cfg = pick_section(cfg_root, section)
        apply_yaml_defaults_to_parser(parser, cfg)

    return parser.parse_args()

