# -*- coding: utf-8 -*-

import os
import re
import sys
import importlib
import subprocess
from pathlib import Path
from types import ModuleType
from loguru import logger
from packaging.version import parse as parse_version


def is_valid_whl_filename(package_name):
    """
    验证WHL文件名是否安全（聚焦防范命令注入攻击）

    Args:
        package_name (str): 要验证的whl文件名

    Returns:
        bool: True表示安全，False表示包含危险字符
    """

    # 禁止路径分隔符
    if os.path.sep in package_name or (os.path.altsep and os.path.altsep in package_name):
        return False

    # 定义危险字符黑名单
    dangerous_pattern = re.compile(r"""
        [                        # 匹配任意以下字符
          ; & | `                # 命令分隔符
          $ () {} <>             # 变量展开/命令替换
          \] \[                  # 特殊符号
          ! \\                   # 历史扩展/转义符
          '"*?#\s                # 引号/通配符/空格
        ]
    """, re.VERBOSE)

    if dangerous_pattern.search(package_name):
        return False

    return True


class PackageNotFoundError(Exception):
    pass


class LazyLoader(ModuleType):
    def __init__(self,
                 package_name,
                 module_name=None,
                 whl_path="/dataset/ops_whl",
                 exact_version=None,
                 force_reinstall=False
                 ):
        """
        :param package_name: WHL包名称中的模块名称部分（一般是模块名称_替换为-）
        :param module_name: WHL包安装后，可用于import的模块名称, 当whl包名称和import名称不一致时，填写local_name.
        :param whl_path: WHL文件所在目录
        :param exact_version: 精确版本要求
        :param force_reinstall: 强制重新安装
        """
        try:
            frame = sys._getframe(1)
            self._parent_globals = frame.f_globals
        except (AttributeError, ValueError) as e:
            logger.error(f"Failed to get stack frame: {e}")
            raise RuntimeError("Stack frame retrieval failed") from e

        self._module_name = module_name if module_name else package_name
        self._package_name = package_name

        self.whl_path = Path(whl_path).resolve()
        self.exact_version = exact_version

        self.force_reinstall = force_reinstall
        self._cached_module = None

        # 注册别名到父级命名空间
        self._parent_globals[self._module_name] = self
        super().__init__(self._module_name)

    def __getattr__(self, name):
        if self._cached_module is None:
            self._cached_module = self._load_module()
        return getattr(self._cached_module, name)

    def __dir__(self):
        return dir(self._load_module())

    def _load_module(self):
        """模块加载逻辑"""

        if self._cached_module is not None:
            return self._cached_module

        package_name: str = self._package_name.split('.')[0]
        if not is_valid_whl_filename(package_name):
            logger.error(f"Invalid package_name: {package_name}")
            raise RuntimeError("Invalide package_name, please check it again!")

        module_name = self._module_name if self._module_name else package_name.replace("_", "-")

        need_install = False

        try:
            if not self.force_reinstall:
                module = importlib.import_module(module_name)
                self._cached_module = module
                self._register_alias(module)
                return module
        except ImportError:
            need_install = True

        if self.force_reinstall:
            # 强制安装时的版本检查
            installed = self._check_package_exists(package_name)
            if installed and self.exact_version:
                installed_version = self._get_installed_version(package_name)
                if parse_version(installed_version) != parse_version(self.exact_version):
                    logger.info(f"Version mismatch detected: {installed_version} vs {self.exact_version}")
                    need_install = True
            else:
                need_install = True

        if need_install:
            self._pip_install_package(package_name)
            module = importlib.import_module(module_name)
            self._cached_module = module
            self._register_alias(module)
        else:
            # 版本检查通过，无需再次安装
            module = importlib.import_module(module_name)
            self._cached_module = module
            self._register_alias(module)

        return self._cached_module

    def _register_alias(self, module):
        """注册本地别名 """
        self._parent_globals[self._module_name] = module
        sys.modules[self._module_name] = module

    def _check_package_exists(self, package_name):
        """增强版包检查"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", package_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except subprocess.SubprocessError as e:
            logger.error(f"Package check failed: {e}")
            return False

    def _get_installed_version(self, package_name):
        """获取已安装版本 """
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True
        )
        for line in result.stdout.split('\n'):
            if line.startswith('Version:'):
                return line.split()[-1]
        raise PackageNotFoundError()

    def _pip_install_package(self, package_name: str):
        """安装逻辑 """

        if not self.whl_path.exists():
            raise FileNotFoundError(f"WHL directory not found: {self.whl_path}")

        whl_files = list(self.whl_path.glob(f"{package_name}*.whl"))
        if not whl_files:
            raise RuntimeError(f"No WHL files found for {package_name}")

        # 版本过滤
        if self.exact_version:
            pattern = re.compile(
                rf'^{re.escape(package_name)}-{re.escape(self.exact_version)}-\S*\.whl$',
                re.IGNORECASE
            )
            whl_files = [f for f in whl_files if pattern.match(f.name)]

        # 选择最新版本
        whl_versions = []
        for f in whl_files:
            try:
                version = self._extract_version(f)
                whl_versions.append((f, version))
            except ValueError:
                continue

        if not whl_versions:
            raise FileNotFoundError("No valid WHL files")

        whl_versions.sort(key=lambda x: x[1], reverse=True)
        target_whl = whl_versions[0][0]

        # 执行安装
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "--no-index",
                f"--find-links={self.whl_path}",
                str(target_whl)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            logger.info(f"Successfully installed {target_whl}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Installation failed: {e}")
            raise RuntimeError(f"Installation failed: {e}") from e

    def _extract_version(self, filename):
        """版本解析 """

        version_pattern = r"(\d+([.]\d+)+([ab]|rc\d+)*([.]post\d+)*([.]dev\d+)*)"

        match = re.search(
            rf"^{re.escape(self._package_name)}-({version_pattern})",
            filename.name,
            re.IGNORECASE
        )
        if not match:
            raise ValueError(f"Invalid version format: {filename.name}")
        return parse_version(match.group(1))
