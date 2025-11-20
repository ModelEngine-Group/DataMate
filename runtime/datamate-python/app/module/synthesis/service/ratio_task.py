from typing import List, Optional, Dict, Any
import random
import json
import os
import shutil
import asyncio

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.ratio_task import RatioInstance, RatioRelation
from app.db.models import Dataset, DatasetFiles
from app.db.session import AsyncSessionLocal
from app.module.dataset.schema.dataset_file import DatasetFileTag
from app.module.shared.schema import TaskStatus
from app.module.synthesis.schema.ratio_task import FilterCondition

logger = get_logger(__name__)


class RatioTaskService:
    """Service for Ratio Task DB operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(
        self,
        *,
        name: str,
        description: Optional[str],
        totals: int,
        config: List[Dict[str, Any]],
        target_dataset_id: Optional[str] = None,
    ) -> RatioInstance:
        """Create a ratio task instance and its relations.

        config item format: {"dataset_id": str, "counts": int, "filter_conditions": str}
        """
        logger.info(f"Creating ratio task: name={name}, totals={totals}, items={len(config or [])}")

        instance = RatioInstance(
            name=name,
            description=description,
            totals=totals,
            target_dataset_id=target_dataset_id,
            status="PENDING",
        )
        self.db.add(instance)
        await self.db.flush()  # populate instance.id

        for item in config or []:
            relation = RatioRelation(
                ratio_instance_id=instance.id,
                source_dataset_id=item.get("dataset_id"),
                counts=int(item.get("counts", 0)),
                filter_conditions=json.dumps({
                    'date_range': item.get("filter_conditions").date_range,
                    'label': item.get("filter_conditions").label,
                })
            )
            logger.info(f"Relation created: {relation.id}, {relation}, {item}, {config}")
            self.db.add(relation)

        await self.db.commit()
        await self.db.refresh(instance)
        logger.info(f"Ratio task created: {instance.id}")
        return instance

    # ========================= Execution (Background) ========================= #

    @staticmethod
    async def execute_dataset_ratio_task(instance_id: str) -> None:
        """Execute a ratio task in background.

        Supported ratio_method:
        - DATASET: randomly select counts files from each source dataset
        - TAG: randomly select counts files matching relation.filter_conditions tags

        Steps:
        - Mark instance RUNNING
        - For each relation: fetch ACTIVE files, optionally filter by tags
        - Copy selected files into target dataset
        - Update dataset statistics and mark instance SUCCESS/FAILED
        """
        async with AsyncSessionLocal() as session:  # type: AsyncSession
            try:
                # Load instance and relations
                inst_res = await session.execute(select(RatioInstance).where(RatioInstance.id == instance_id))
                instance: Optional[RatioInstance] = inst_res.scalar_one_or_none()
                if not instance:
                    logger.error(f"Ratio instance not found: {instance_id}")
                    return
                logger.info(f"start execute ratio task: {instance_id}")

                rel_res = await session.execute(
                    select(RatioRelation).where(RatioRelation.ratio_instance_id == instance_id)
                )
                relations: List[RatioRelation] = list(rel_res.scalars().all())

                # Mark running
                instance.status = TaskStatus.RUNNING.name

                # Load target dataset
                ds_res = await session.execute(select(Dataset).where(Dataset.id == instance.target_dataset_id))
                target_ds: Optional[Dataset] = ds_res.scalar_one_or_none()
                if not target_ds:
                    logger.error(f"Target dataset not found for instance {instance_id}")
                    instance.status = TaskStatus.FAILED.name
                    return

                added_count, added_size = await RatioTaskService.handle_ratio_relations(relations,session, target_ds)

                # Update target dataset statistics
                target_ds.file_count = (target_ds.file_count or 0) + added_count  # type: ignore
                target_ds.size_bytes = (target_ds.size_bytes or 0) + added_size  # type: ignore
                # If target dataset has files, mark it ACTIVE
                if (target_ds.file_count or 0) > 0:  # type: ignore
                    target_ds.status = "ACTIVE"

                # Done
                instance.status = TaskStatus.COMPLETED.name
                logger.info(f"Dataset ratio execution completed: instance={instance_id}, files={added_count}, size={added_size}, {instance.status}")

            except Exception as e:
                logger.exception(f"Dataset ratio execution failed for {instance_id}: {e}")
                try:
                    # Try mark failed
                    inst_res = await session.execute(select(RatioInstance).where(RatioInstance.id == instance_id))
                    instance = inst_res.scalar_one_or_none()
                    if instance:
                        instance.status = TaskStatus.FAILED.name
                finally:
                    pass
            finally:
                await session.commit()

    @staticmethod
    async def handle_ratio_relations(relations: list[RatioRelation], session, target_ds: Dataset) -> tuple[int, int]:
        # Preload existing target file paths for deduplication
        existing_path_rows = await session.execute(
            select(DatasetFiles.file_path).where(DatasetFiles.dataset_id == target_ds.id)
        )
        existing_paths = set(p for p in existing_path_rows.scalars().all() if p)

        added_count = 0
        added_size = 0

        for rel in relations:
            if not rel.source_dataset_id or not rel.counts or rel.counts <= 0:
                continue

            files = await RatioTaskService.get_files(rel, session)

            if not files:
                continue

            pick_n = min(rel.counts or 0, len(files))
            chosen = random.sample(files, pick_n) if pick_n < len(files) else files

            # Copy into target dataset with de-dup by target path
            for f in chosen:
                await RatioTaskService.handle_selected_file(existing_paths, f, session, target_ds)
                added_count += 1
                added_size += int(f.file_size or 0)

            # Periodically flush to avoid huge transactions
            await session.flush()
        return added_count, added_size

    @staticmethod
    async def handle_selected_file(existing_paths: set[Any], f, session, target_ds: Dataset):
        src_path = f.file_path
        dst_prefix = f"/dataset/{target_ds.id}"
        file_name = RatioTaskService.get_new_file_name(dst_prefix, existing_paths, f)

        new_path = dst_prefix + file_name
        dst_dir = os.path.dirname(new_path)
        await asyncio.to_thread(os.makedirs, dst_dir, exist_ok=True)
        await asyncio.to_thread(shutil.copy2, src_path, new_path)

        new_file = DatasetFiles(
            dataset_id=target_ds.id,  # type: ignore
            file_name=file_name,
            file_path=new_path,
            file_type=f.file_type,
            file_size=f.file_size,
            check_sum=f.check_sum,
            tags=f.tags,
            dataset_filemetadata=f.dataset_filemetadata,
            status="ACTIVE",
        )
        session.add(new_file)
        existing_paths.add(new_path)

    @staticmethod
    def get_new_file_name(dst_prefix: str, existing_paths: set[Any], f) -> str:
        file_name = f.file_name
        new_path = dst_prefix + file_name

        # Handle file path conflicts by appending a number to the filename
        if new_path in existing_paths:
            file_name_base, file_ext = os.path.splitext(file_name)
            counter = 1
            original_file_name = file_name
            while new_path in existing_paths:
                file_name = f"{file_name_base}_{counter}{file_ext}"
                new_path = f"{dst_prefix}{file_name}"
                counter += 1
                if counter > 1000:  # Safety check to prevent infinite loops
                    logger.error(f"Could not find unique filename for {original_file_name} after 1000 attempts")
                    break
        return file_name

    @staticmethod
    async def get_files(rel: RatioRelation, session) -> list[Any]:
        # Fetch all files for the source dataset (ACTIVE only)
        files_res = await session.execute(
            select(DatasetFiles).where(
                DatasetFiles.dataset_id == rel.source_dataset_id,
                DatasetFiles.status == "ACTIVE",
            )
        )
        files = list(files_res.scalars().all())

        # TAG mode: filter by tags according to relation.filter_conditions
        conditions = RatioTaskService._parse_conditions(rel.filter_conditions)
        if conditions:
            files = [f for f in files if RatioTaskService._filter_file(f, conditions)]
        return files

    # ------------------------- helpers for TAG filtering ------------------------- #

    @staticmethod
    def _parse_conditions(conditions: Optional[str]) -> Optional[FilterCondition]:
        """Parse filter_conditions JSON string into a FilterCondition object.

        Args:
            conditions: JSON string containing filter conditions

        Returns:
            FilterCondition object if conditions is not None/empty, otherwise None
        """
        if not conditions:
            return None
        try:
            data = json.loads(conditions)
            return FilterCondition(**data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse filter conditions: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating FilterCondition: {e}")
            return None

    @staticmethod
    def _filter_file(file: DatasetFiles, conditions: FilterCondition) -> bool:
        if not conditions:
            return True
        logger.info(f"start filter file: {file}, conditions: {conditions}")

        # Check data range condition if provided
        if conditions.date_range:
            try:
                from datetime import datetime, timedelta
                data_range_days = int(conditions.date_range)
                if data_range_days > 0:
                    cutoff_date = datetime.now() - timedelta(days=data_range_days)
                    if file.tags_updated_at and file.tags_updated_at < cutoff_date:
                        return False
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid data_range value: {conditions.date_range}", e)
                return False

        # Check label condition if provided
        if conditions.label:
            tags = file.tags
            if not tags:
                return False
            try:
                # tags could be a list of strings or list of objects with 'name'
                tag_names = RatioTaskService.get_all_tags(tags)
                return conditions.label in tag_names
            except Exception as e:
                logger.exception(f"Failed to get tags for {file}", e)
                return False

        return True

    @staticmethod
    def get_all_tags(tags) -> set[str]:
        """获取所有处理后的标签字符串列表"""
        all_tags = set()
        if not tags:
            return all_tags

        file_tags = []
        for tag_data in tags:
            # 处理可能的命名风格转换（下划线转驼峰）
            processed_data = {}
            for key, value in tag_data.items():
                # 将驼峰转为下划线以匹配 Pydantic 模型字段
                processed_data[key] = value
            # 创建 DatasetFileTag 对象
            file_tag = DatasetFileTag(**processed_data)
            file_tags.append(file_tag)

        for file_tag in file_tags:
            for tag_data in file_tag.get_tags():
                all_tags.add(tag_data)
        return all_tags
