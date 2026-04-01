import datetime
import json
import os
import time
from typing import Iterable, List, Sequence, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.data_synthesis import (
    DataSynthInstance,
    DataSynthesisFileInstance,
    SynthesisData,
)
from app.db.models.dataset_management import Dataset, DatasetFiles

logger = get_logger(__name__)


class SynthesisExportError(Exception):
    """Raised when exporting synthesis data to dataset fails."""


class SynthesisDatasetExporter:
    """Export synthesis data of a task into an existing dataset.

    Export rules:
    - Dimension: original file (DatasetFiles)
    - One JSONL file per original file
    - JSONL file name is exactly the same as the original file name
    - Support format conversion: alpaca, sharegpt, raw
    """

    SUPPORTED_FORMATS = ["alpaca", "sharegpt", "raw"]
    DEFAULT_FORMAT = "alpaca"

    def __init__(self, db: AsyncSession, format: str = "alpaca"):
        self._db = db
        self._format = format if format in self.SUPPORTED_FORMATS else self.DEFAULT_FORMAT

    async def export_task_to_dataset(
        self,
        task_id: str,
        dataset_id: str,
    ) -> Dataset:
        """Export the full synthesis data of the given task into an existing dataset.

        Optimized to process one file at a time to reduce memory usage.
        """
        task = await self._db.get(DataSynthInstance, task_id)
        if not task:
            raise SynthesisExportError(f"Synthesis task {task_id} not found")

        dataset = await self._db.get(Dataset, dataset_id)
        if not dataset:
            raise SynthesisExportError(f"Dataset {dataset_id} not found")

        file_instances = await self._load_file_instances(task_id)
        if not file_instances:
            raise SynthesisExportError("No synthesis file instances found for task")

        base_path = self._ensure_dataset_path(dataset)

        created_files: list[DatasetFiles] = []
        total_size = 0

        # 一个文件一个文件处理，避免一次性加载所有合成数据
        for file_instance in file_instances:
            records = await self._load_synthesis_data_for_file(file_instance.id)
            if not records:
                continue

            # 归档文件名称：原始文件名称.xxx -> 原始文件名称.jsonl
            original_name = file_instance.file_name or "unknown"
            base_name, _ = os.path.splitext(original_name)
            archived_file_name = f"{base_name}.jsonl"

            file_path = os.path.join(base_path, archived_file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            self._write_jsonl(file_path, records, self._format)

            # 计算文件大小
            try:
                file_size = os.path.getsize(file_path)
            except OSError:
                file_size = 0

            df = DatasetFiles(
                dataset_id=dataset.id,
                file_name=archived_file_name,
                file_path=file_path,
                file_type="jsonl",
                file_size=file_size,
                last_access_time=datetime.datetime.now(),
            )
            self._db.add(df)
            created_files.append(df)
            total_size += file_size

        # 更新数据集的文件数、总大小和状态
        if created_files:
            dataset.file_count = (dataset.file_count or 0) + len(created_files)
            dataset.size_bytes = (dataset.size_bytes or 0) + total_size
            dataset.status = "ACTIVE"

        await self._db.commit()

        logger.info(
            "Exported synthesis task %s to dataset %s with %d files (total %d bytes)",
            task_id,
            dataset.id,
            len(created_files),
            total_size,
        )

        return dataset

    async def _load_file_instances(self, task_id: str) -> Sequence[DataSynthesisFileInstance]:
        result = await self._db.execute(
            select(DataSynthesisFileInstance).where(
                DataSynthesisFileInstance.synthesis_instance_id == task_id
            )
        )
        return result.scalars().all()

    async def _load_synthesis_data_for_file(
        self, file_instance_id: str
    ) -> List[dict]:
        """Load all synthesis data records for a single file instance.

        Each returned item is a plain JSON-serialisable dict based on SynthesisData.data.
        """
        result = await self._db.execute(
            select(SynthesisData).where(
                SynthesisData.synthesis_file_instance_id == file_instance_id
            )
        )
        rows: Sequence[SynthesisData] = result.scalars().all()

        records: List[dict] = []
        for row in rows:
            payload = row.data or {}
            records.append(payload)
        return records

    def _write_jsonl(self, path: str, records: Iterable[dict], format: str | None = None) -> None:
        """写入JSONL文件

        Args:
            path: 输出文件路径
            records: 数据记录迭代器
            format: 导出格式 (alpaca/sharegpt/raw)
        """
        fmt = format or self._format
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for record in records:
                formatted = self._format_record(record, fmt)
                f.write(json.dumps(formatted, ensure_ascii=False))
                f.write("\n")

    def _format_record(self, record: dict, format: str) -> dict:
        """根据格式转换记录

        Args:
            record: 原始记录
            format: 目标格式

        Returns:
            格式化后的记录
        """
        if format == "alpaca":
            return self._format_as_alpaca(record)
        elif format == "sharegpt":
            return self._format_as_sharegpt(record)
        else:
            return self._format_as_raw(record)

    def _format_as_alpaca(self, record: dict) -> dict:
        """转换为Alpaca格式

        Alpaca格式：
        {
            "instruction": "指令",
            "input": "输入",
            "output": "输出"
        }
        """
        return {
            "instruction": record.get("instruction", ""),
            "output": record.get("output", ""),
        }

    def _format_as_sharegpt(self, record: dict) -> dict:
        """转换为ShareGPT格式

        ShareGPT格式：
        {
            "conversations": [
                {"from": "human", "value": "用户消息"},
                {"from": "gpt", "value": "模型回复"}
            ]
        }
        """
        instruction = record.get("instruction", "")
        output = record.get("output", "")
        input_text = record.get("input", "")

        conversations = [
            {"from": "human", "value": instruction},
            {"from": "gpt", "value": output},
        ]

        result = {"conversations": conversations}

        if input_text:
            result["context"] = input_text

        return result

    def _format_as_raw(self, record: dict) -> dict:
        """原始格式 - 直接输出"""
        return record

    @staticmethod
    def _ensure_dataset_path(dataset: Dataset) -> str:
        """Ensure dataset.path is available and the directory exists.

        The actual value of dataset.path should come from Dataset's default
        path generation logic or external configuration, not from the
        synthesis task's result_data_location.
        """
        if not dataset.path:
            raise SynthesisExportError("Dataset path is empty")
        os.makedirs(dataset.path, exist_ok=True)
        return dataset.path
