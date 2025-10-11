# -*- coding: utf-8 -*-

import sys
import re
import subprocess
from pathlib import Path
from typing import Optional
from loguru import logger
from packaging.version import parse as parse_version, Version


def install_whl(
        package_name: str,
        whl_path: str,
        exact_version: Optional[str] = None,
        filename_pattern: Optional[str] = None,
        force_reinstall: bool = False
) -> None:
    """

    :param package_name: eg: ("zh_core_web_sm")
    :param whl_path: WHL file save path
    :param exact_version: version number
    :param filename_pattern: custom filename pattern for REGEX
    :param force_reinstall: which decide to overlap the original number or not (default: False)
    """

    whl_dir = Path(whl_path).resolve()
    whl_files = _get_whl_files(exact_version, filename_pattern, package_name, whl_dir)

    # 语义化版本排序
    target_whl = _sort_whl_files(whl_files)

    # 安装命令
    cmd = [
        sys.executable, "-m", "pip", "install",
        "--no-index",
        f"--find-links={whl_dir}",
        str(target_whl)
    ]
    if force_reinstall:
        cmd.append("--force-reinstall")

    try:
        subprocess.check_call(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )
        logger.info(f"Successfully installed {target_whl.name}")
    except subprocess.CalledProcessError as e:
        error_msg = (
            f"Installation failed for {package_name}\n"
            f"Possible reasons:\n"
            f"1. Missing dependencies in {whl_dir}\n"
            f"2. Incompatible Python version\n"
            f"3. Platform mismatch (e.g., x86 vs ARM)"
        )
        raise RuntimeError(error_msg) from e


def _sort_whl_files(whl_files):
    whl_versions = []
    logger.info(f"[load_offline_module]whl_files: {whl_files}")
    for f in whl_files:
        try:
            version = _extract_version(f)
            whl_versions.append((f, version))
        except ValueError as e:
            logger.warning(f"Skipping invalid file {f.name}: {e}")
            continue
    if not whl_versions:
        raise FileNotFoundError("No valid WHL files with parseable versions")
    whl_versions.sort(key=lambda x: x[1], reverse=True)
    target_whl = whl_versions[0][0]
    return target_whl


def _get_whl_files(exact_version, filename_pattern, package_name, whl_dir):
    # 正则表达式
    if filename_pattern:
        pattern = filename_pattern
    else:
        if exact_version:
            version_part = re.escape(exact_version)
            pattern = rf"^{re.escape(package_name)}-{version_part}-\S*\.whl$"
        else:
            pattern = rf"^{re.escape(package_name)}\S*\.whl$"
    regex = re.compile(pattern, re.IGNORECASE)
    whl_files = [f for f in whl_dir.glob("*.whl") if regex.match(f.name)]
    if not whl_files:
        available_files = "\n".join([f.name for f in whl_dir.glob("*.whl")])
        raise FileNotFoundError(
            f"No matching WHL found for {package_name} in {whl_dir}\n"
            f"Available files:\n{available_files}"
        )
    return whl_files


def _extract_version(filename: Path) -> Version:
    """从文件名提取语义化版本（"""

    match = re.search(
        r"-(\d+([.]\d+)+([ab]|rc\d+)*([.]post\d+)*([.]dev\d+)*)-",
        filename.name
    )
    if not match:
        raise ValueError(f"Invalid version format: {filename.name}")
    return parse_version(match.group(1))
