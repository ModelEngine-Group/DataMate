import datetime
import json
import os
import time
from typing import Iterable, List, Sequence, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.data_synthesis import (
    DataSynthesisInstance,
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
    """

    def __init__(self, db: AsyncSession):
        self._db = db

    async def export_task_to_dataset(
        self,
        task_id: str,
        dataset_id: str,
    ) -> Dataset:
        """Export the full synthesis data of the given task into an existing dataset.

        Optimized to process one file at a time to reduce memory usage.
        """
        task = await self._db.get(DataSynthesisInstance, task_id)
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
            self._write_jsonl(file_path, records)

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
                last_access_time=datetime.datetime.now(datetime.UTC),
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

    @staticmethod
    def _write_jsonl(path: str, records: Iterable[dict]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False))
                f.write("\n")

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
