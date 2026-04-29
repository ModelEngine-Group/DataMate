"""
资源感知并发计算工具

根据系统 CPU 和内存资源动态计算最优并发数
适配全闪存储等高性能存储场景
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 尝试导入 psutil，失败则使用 os.cpu_count
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logger.warning("psutil not available, falling back to os.cpu_count() for CPU detection")


def get_cpu_count(logical: bool = True) -> int:
    """获取 CPU 核心数
    
    Args:
        logical: 是否返回逻辑核心数（超线程），False返回物理核心数
        
    Returns:
        CPU 核心数，无法检测时返回默认值 4
    """
    if HAS_PSUTIL:
        count = psutil.cpu_count(logical=logical)
        if count:
            return count
    
    # 回退到 os.cpu_count()
    count = os.cpu_count()
    return count if count else 4


def get_available_memory_gb() -> float:
    """获取可用内存（GB）
    
    Returns:
        可用内存大小（GB），无法检测时返回默认值 8.0
    """
    if HAS_PSUTIL:
        mem = psutil.virtual_memory()
        return mem.available / (1024 ** 3)
    
    # 无法检测，返回保守默认值
    logger.warning("psutil not available, using default memory estimate")
    return 8.0


def calculate_optimal_concurrent(
    min_concurrent: int = 8,
    max_concurrent: int = 128,
    cpu_factor: float = 4.0,
    memory_per_task_mb: int = 32,
    memory_reserve_ratio: float = 0.2,
) -> int:
    """根据系统资源计算最优并发数
    
    计算逻辑：
    1. 基于 CPU 核心数：并发数 = CPU核心数 × cpu_factor
    2. 基于内存限制：可用内存 × (1-reserve_ratio) ÷ memory_per_task
    3. 最终取两者最小值，并限制在 [min_concurrent, max_concurrent] 范围内
    
    Args:
        min_concurrent: 并发下限
        max_concurrent: 并发上限
        cpu_factor: CPU核心系数（全闪存储建议4.0）
        memory_per_task_mb: 每任务预估内存占用（MB）
        memory_reserve_ratio: 内存安全保留比例
        
    Returns:
        计算得出的最优并发数
    """
    # 获取 CPU 核心数
    cpu_count = get_cpu_count(logical=True)
    
    # 基于 CPU 计算并发数
    cpu_based_concurrent = int(cpu_count * cpu_factor)
    
    # 获取可用内存
    available_memory_gb = get_available_memory_gb()
    
    # 计算可用于并发任务的内存（扣除保留部分）
    usable_memory_gb = available_memory_gb * (1 - memory_reserve_ratio)
    usable_memory_mb = usable_memory_gb * 1024
    
    # 基于内存计算最大并发数
    memory_based_concurrent = int(usable_memory_mb / memory_per_task_mb)
    
    # 取两者最小值（避免内存耗尽）
    calculated_concurrent = min(cpu_based_concurrent, memory_based_concurrent)
    
    # 限制在范围内
    final_concurrent = max(min_concurrent, min(max_concurrent, calculated_concurrent))
    
    # 记录计算过程
    logger.info(
        f"Concurrency calculation: "
        f"CPU cores={cpu_count}, CPU-based={cpu_based_concurrent}, "
        f"Available memory={available_memory_gb:.1f}GB, Memory-based={memory_based_concurrent}, "
        f"Final concurrent={final_concurrent} (range=[{min_concurrent}, {max_concurrent}])"
    )
    
    return final_concurrent


def get_concurrent_for_ratio_copy(settings) -> int:
    """获取配比文件复制的并发数
    
    Args:
        settings: 配置实例
        
    Returns:
        并发数（动态计算或固定值）
    """
    if not settings.ratio_copy_dynamic_concurrent:
        return settings.ratio_copy_fixed_concurrent
    
    return calculate_optimal_concurrent(
        min_concurrent=settings.ratio_copy_min_concurrent,
        max_concurrent=settings.ratio_copy_max_concurrent,
        cpu_factor=settings.ratio_copy_cpu_factor,
        memory_per_task_mb=settings.ratio_copy_memory_per_task_mb,
        memory_reserve_ratio=settings.ratio_copy_memory_reserve_ratio,
    )


def get_system_resource_info() -> dict:
    """获取系统资源信息（用于日志和调试）
    
    Returns:
        系统资源信息字典
    """
    cpu_logical = get_cpu_count(logical=True)
    cpu_physical = get_cpu_count(logical=False) if HAS_PSUTIL else cpu_logical
    
    if HAS_PSUTIL:
        mem = psutil.virtual_memory()
        return {
            "cpu_logical_cores": cpu_logical,
            "cpu_physical_cores": cpu_physical,
            "memory_total_gb": round(mem.total / (1024 ** 3), 2),
            "memory_available_gb": round(mem.available / (1024 ** 3), 2),
            "memory_used_percent": round(mem.percent, 1),
            "psutil_available": True,
        }
    
    return {
        "cpu_logical_cores": cpu_logical,
        "cpu_physical_cores": cpu_physical,
        "memory_available_gb": get_available_memory_gb(),
        "psutil_available": False,
    }