"""数据导出模块 - 支持多种格式导出"""
import json
import os
from abc import ABC, abstractmethod
from typing import Any, Iterable

from app.db.models.data_synthesis import (
    DataSynthesisFileInstance,
    SynthesisData,
)
from app.db.session import logger


class ExportFormatHandler(ABC):
    """导出格式处理器基类"""

    @abstractmethod
    def format_record(self, data: dict[str, Any]) -> dict[str, Any]:
        """格式化单条记录

        Args:
            data: 原始合成数据

        Returns:
            格式化后的数据
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        pass


class AlpacaFormatHandler(ExportFormatHandler):
    """Alpaca格式处理器

    Alpaca格式：
    {
        "instruction": "指令",
        "input": "输入",
        "output": "输出"
    }
    """

    def format_record(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "instruction": data.get("instruction", ""),
            "input": data.get("input", ""),
            "output": data.get("output", ""),
        }

    def get_file_extension(self) -> str:
        return ".jsonl"


class ShareGPTFormatHandler(ExportFormatHandler):
    """ShareGPT格式处理器

    ShareGPT格式：
    {
        "conversations": [
            {"from": "human", "value": "用户消息"},
            {"from": "gpt", "value": "模型回复"}
        ]
    }
    """

    def format_record(self, data: dict[str, Any]) -> dict[str, Any]:
        instruction = data.get("instruction", "")
        output = data.get("output", "")
        input_text = data.get("input", "")

        conversations = [
            {"from": "human", "value": instruction},
            {"from": "gpt", "value": output},
        ]

        result = {"conversations": conversations}

        if input_text:
            result["context"] = input_text

        return result

    def get_file_extension(self) -> str:
        return ".jsonl"


class RawFormatHandler(ExportFormatHandler):
    """原始格式处理器 - 直接输出原始数据"""

    def format_record(self, data: dict[str, Any]) -> dict[str, Any]:
        return data

    def get_file_extension(self) -> str:
        return ".jsonl"


class DataExporter:
    """数据导出器"""

    FORMAT_HANDLERS = {
        "alpaca": AlpacaFormatHandler,
        "sharegpt": ShareGPTFormatHandler,
        "raw": RawFormatHandler,
    }

    def __init__(self, format_type: str = "alpaca"):
        handler_class = self.FORMAT_HANDLERS.get(format_type, AlpacaFormatHandler)
        self.handler = handler_class()

    def write_jsonl(
        self,
        file_path: str,
        records: Iterable[dict[str, Any]],
    ) -> int:
        """写入JSONL文件

        Args:
            file_path: 输出文件路径
            records: 数据记录迭代器

        Returns:
            写入的记录数
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        count = 0
        with open(file_path, "w", encoding="utf-8") as f:
            for record in records:
                formatted = self.handler.format_record(record)
                f.write(json.dumps(formatted, ensure_ascii=False))
                f.write("\n")
                count += 1

        logger.info(f"Exported {count} records to {file_path}")
        return count

    def get_file_extension(self) -> str:
        return self.handler.get_file_extension()


async def export_synthesis_data_to_file(
    file_instance: DataSynthesisFileInstance,
    synthesis_data_list: list[SynthesisData],
    output_dir: str,
    format_type: str = "alpaca",
) -> tuple[str, int]:
    """导出合成数据到文件

    Args:
        file_instance: 文件任务实例
        synthesis_data_list: 合成数据列表
        output_dir: 输出目录
        format_type: 导出格式

    Returns:
        (文件路径, 记录数)
    """
    exporter = DataExporter(format_type)

    # 构建文件名
    original_name = file_instance.file_name or "unknown"
    base_name, _ = os.path.splitext(original_name)
    file_name = f"{base_name}{exporter.get_file_extension()}"
    file_path = os.path.join(output_dir, file_name)

    # 提取数据
    records = [row.data or {} for row in synthesis_data_list]

    # 写入文件
    count = exporter.write_jsonl(file_path, records)

    return file_path, count


def get_supported_formats() -> list[dict[str, str]]:
    """获取支持的导出格式列表"""
    return [
        {"type": "alpaca", "name": "Alpaca", "extension": ".jsonl"},
        {"type": "sharegpt", "name": "ShareGPT", "extension": ".jsonl"},
        {"type": "raw", "name": "原始格式", "extension": ".jsonl"},
    ]