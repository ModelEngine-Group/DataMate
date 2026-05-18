#!/usr/bin/env python3
"""
运行 WeNet 识别脚本的包装器
解决 WeNet 模块导入问题
"""

import sys
import os
from pathlib import Path

def main():
    """主函数"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent
    
    # 添加 WeNet 到 Python 路径
    wenet_root = project_root / "local_libs" / "wenet"
    
    # 将 wenet 根目录添加到系统路径
    if str(wenet_root) not in sys.path:
        sys.path.insert(0, str(wenet_root))
    
    # 将 wenet 的父目录也添加到路径（因为 wenet 模块在 wenet/wenet/ 中）
    wenet_module_path = wenet_root / "wenet"
    if str(wenet_module_path) not in sys.path:
        sys.path.insert(0, str(wenet_module_path))
    
    # 现在导入 WeNet 的 recognize 模块并运行
    try:
        from wenet.bin.recognize import main as wenet_main
        wenet_main()
    except ImportError as e:
        print(f"[ERROR] 无法导入 WeNet 模块: {e}")
        print(f"[INFO] Python 路径: {sys.path}")
        sys.exit(1)

if __name__ == "__main__":
    main()