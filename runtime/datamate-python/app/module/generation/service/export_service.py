"""
数据导出服务 - 负责将合成数据导出为各种格式
"""
import datetime
import json
import os
from typing import Iterable, List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.data_synthesis import (
    DataSynthInstance,
    DataSynthesisFileInstance,
    SynthesisData,
)
from app.db.models.dataset_management import Dataset, DatasetFiles
from app.module.generation.schema.generation import (
    ExportSynthesisDataResponse,
)

logger = get_logger(__name__)


class SynthesisExportError(Exception):
    """导出失败时抛出的异常"""


class SynthesisDatasetExporter:
    """
    数据导出器 - 将合成数据导出为各种格式

    导出规则：
    - 维度：原始文件 (DatasetFiles)
    - 每个原始文件生成一个 JSONL 文件
    - JSONL 文件名称与原始文件名称一致
    - 支持格式转换：alpaca、sharegpt、raw
    """

    SUPPORTED_FORMATS = ["alpaca", "sharegpt", "raw"]
    DEFAULT_FORMAT = "alpaca"

    def __init__(self, db: AsyncSession, format: str = "alpaca", output_path: Optional[str] = None):
        self._db = db
        self._format = format if format in self.SUPPORTED_FORMATS else self.DEFAULT_FORMAT
        self._output_path = output_path

    async def export_task_to_dataset(
        self,
        task_id: str,
        dataset_id: str,
    ) -> Dataset:
        """
        将任务的全部合成数据导出到已有数据集

        Args:
            task_id: 任务 ID
            dataset_id: 目标数据集 ID

        Returns:
            更新后的数据集
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

        for file_instance in file_instances:
            records = await self._load_synthesis_data_for_file(file_instance.id)
            if not records:
                continue

            original_name = file_instance.file_name or "unknown"
            base_name, _ = os.path.splitext(original_name)
            archived_file_name = f"{base_name}.jsonl"

            file_path = os.path.join(base_path, archived_file_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            self._write_jsonl(file_path, records, self._format)

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

    async def export_data(
        self,
        task_id: str,
        file_instance_ids: Optional[List[str]] = None,
    ) -> ExportSynthesisDataResponse:
        """
        将合成数据导出为指定格式的 JSONL 文件

        Args:
            task_id: 任务 ID
            file_instance_ids: 文件实例 ID 列表，为空则导出全部

        Returns:
            导出结果
        """
        if file_instance_ids:
            file_instances = await self._load_specific_file_instances(file_instance_ids)
        else:
            file_instances = await self._load_file_instances(task_id)

        if not file_instances:
            raise SynthesisExportError("No file instances to export")

        output_dir = self._output_path or self._get_default_output_dir()
        os.makedirs(output_dir, exist_ok=True)

        file_paths: List[str] = []
        total_records = 0

        for file_instance in file_instances:
            records = await self._load_synthesis_data_for_file(file_instance.id)
            if not records:
                continue

            original_name = file_instance.file_name or "unknown"
            base_name, _ = os.path.splitext(original_name)
            output_file_name = f"{base_name}.jsonl"

            file_path = os.path.join(output_dir, output_file_name)
            self._write_jsonl(file_path, records, self._format)

            file_paths.append(file_path)
            total_records += len(records)

        return ExportSynthesisDataResponse(
            file_paths=file_paths,
            total_records=total_records,
            format=self._format,
        )

    async def _load_file_instances(self, task_id: str) -> Sequence[DataSynthesisFileInstance]:
        """加载任务下的所有文件实例"""
        result = await self._db.execute(
            select(DataSynthesisFileInstance).where(
                DataSynthesisFileInstance.synthesis_instance_id == task_id
            )
        )
        return result.scalars().all()

    async def _load_specific_file_instances(
        self, file_ids: List[str]
    ) -> Sequence[DataSynthesisFileInstance]:
        """加载指定的文件实例"""
        result = await self._db.execute(
            select(DataSynthesisFileInstance).where(
                DataSynthesisFileInstance.id.in_(file_ids)
            )
        )
        return result.scalars().all()

    async def _load_synthesis_data_for_file(
        self, file_instance_id: str
    ) -> List[dict]:
        """加载单个文件实例的所有合成数据"""
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

    def _write_jsonl(self, path: str, records: Iterable[dict], format: Optional[str] = None) -> None:
        """写入 JSONL 文件"""
        fmt = format or self._format
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for record in records:
                formatted = self._format_record(record, fmt)
                f.write(json.dumps(formatted, ensure_ascii=False))
                f.write("\n")

    def _format_record(self, record: dict, format: str) -> dict:
        """根据格式转换记录"""
        if format == "alpaca":
            return self._format_as_alpaca(record)
        elif format == "sharegpt":
            return self._format_as_sharegpt(record)
        else:
            return self._format_as_raw(record)

    def _format_as_alpaca(self, record: dict) -> dict:
        """转换为 Alpaca 格式"""
        return {
            "instruction": record.get("instruction", ""),
            "output": record.get("output", ""),
        }

    def _format_as_sharegpt(self, record: dict) -> dict:
        """转换为 ShareGPT 格式"""
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
        """原始格式"""
        return record

    def _get_default_output_dir(self) -> str:
        """获取默认输出目录"""
        import tempfile
        return tempfile.gettempdir()

    @staticmethod
    def _ensure_dataset_path(dataset: Dataset) -> str:
        """确保数据集路径存在"""
        if not dataset.path:
            raise SynthesisExportError("Dataset path is empty")
        os.makedirs(dataset.path, exist_ok=True)
        return dataset.path
