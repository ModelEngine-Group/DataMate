from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models import DatasetFiles

from ..client import LabelStudioClient

logger = get_logger(__name__)


class LSAnnotationSyncService:
    """将 Label Studio 项目中的标注结果同步回 DM 数据库。

    约定：
    - Label Studio task.data 中包含由 SyncService 写入的 DM 元信息：
      {"file_id": "...", "dataset_id": "...", "file_path": "...", "original_name": "..."}
    - 对于每个 task，我们会：
      * 读取该 task 的 annotations 列表；
      * 结合 task.predictions 一并写入 t_dm_dataset_files.annotation；
      * 从 annotations/predictions 的 result 字段中提取标签，写入 t_dm_dataset_files.tags；
      * 更新时间戳 tags_updated_at。
    """

    def __init__(self, db: AsyncSession, ls_client: LabelStudioClient) -> None:
        self.db = db
        self.ls_client = ls_client

    async def sync_project_annotations_to_dm(self, project_id: str) -> int:
        """从指定 Label Studio 项目中同步所有任务的标注到 DM 文件表。

        Args:
            project_id: Label Studio 项目 ID（字符串形式）。

        Returns:
            成功更新的文件数量。
        """
        try:
            page_size = getattr(settings, "ls_task_page_size", 1000)
            result = await self.ls_client.get_project_tasks(
                project_id=project_id,
                page=None,
                page_size=page_size,
            )
        except Exception as e:  # pragma: no cover - 防御性日志
            logger.error("Failed to fetch tasks from Label Studio project %s: %s", project_id, e)
            return 0

        if not result:
            logger.warning("No tasks returned for project %s when syncing annotations", project_id)
            return 0

        tasks: List[Dict[str, Any]] = result.get("tasks", [])  # type: ignore[assignment]
        if not tasks:
            logger.info("Project %s has no tasks to sync", project_id)
            return 0

        updated_files = 0

        for task in tasks:
            data: Dict[str, Any] = task.get("data") or {}
            raw_file_id = data.get("file_id")
            if not raw_file_id:
                # 旧任务可能没有 DM file_id，跳过但记录日志
                logger.debug(
                    "Skip LS task %s because data.file_id is missing",
                    task.get("id"),
                )
                continue

            file_id = str(raw_file_id)

            # 获取该任务的 annotations 列表
            annotations: Optional[List[Dict[str, Any]]] = None
            try:
                annotations = await self.ls_client.get_task_annotations(int(task["id"]))  # type: ignore[arg-type]
            except Exception as e:  # pragma: no cover
                logger.error(
                    "Failed to fetch annotations for LS task %s (file_id=%s): %s",
                    task.get("id"),
                    file_id,
                    e,
                )

            predictions: List[Dict[str, Any]] = task.get("predictions") or []

            annotation_payload: Dict[str, Any] = {
                "task": {
                    "id": task.get("id"),
                    "project": task.get("project"),
                    "data": data,
                },
                "annotations": annotations or [],
                "predictions": predictions,
            }

            tags = self._extract_tags_from_results(
                annotations or [],
                predictions,
            )

            success = await self._update_dataset_file(file_id, tags, annotation_payload)
            if success:
                updated_files += 1

        logger.info(
            "Synced annotations from LS project %s to DM, updated %d files",
            project_id,
            updated_files,
        )
        return updated_files

    async def _update_dataset_file(
        self,
        file_id: str,
        tags: List[Dict[str, Any]],
        annotation: Dict[str, Any],
    ) -> bool:
        """将提取出的 tags 与 annotation 写回 t_dm_dataset_files。

        直接更新 DatasetFiles.tags / tags_updated_at / annotation 字段，
        不走模板驱动的转换逻辑（模板转换在用户主动批量更新时使用）。
        """
        try:
            result = await self.db.execute(
                select(DatasetFiles).where(DatasetFiles.id == file_id)
            )
            record = result.scalar_one_or_none()

            if not record:
                logger.warning("Dataset file not found when syncing LS annotations: %s", file_id)
                return False

            update_time = datetime.utcnow()
            record.tags = tags  # type: ignore[assignment]
            record.tags_updated_at = update_time  # type: ignore[assignment]
            # annotation 可能较大，但为 JSONB，直接整体覆盖
            setattr(record, "annotation", annotation)

            await self.db.commit()
            await self.db.refresh(record)

            logger.debug(
                "Updated DM file %s with %d tags from LS annotations",
                file_id,
                len(tags),
            )
            return True

        except Exception as e:  # pragma: no cover
            logger.error("Failed to update DM file %s from LS annotations: %s", file_id, e)
            try:
                await self.db.rollback()
            except Exception:
                pass
            return False

    @staticmethod
    def _extract_tags_from_results(
        annotations: List[Dict[str, Any]],
        predictions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """从 annotations 和 predictions 的 result 字段中提取通用标签结构。

        输出格式与 DM 前端当前解析逻辑兼容：
        - 每个元素包含: id/type/from_name/values；
        - 其中 values 是一个字典，键通常与 type 一致，例如 "rectanglelabels"；
        - 前端通过 tag.values[tag.type] 提取字符串标签集合。
        """

        def iter_results() -> List[Dict[str, Any]]:
            res: List[Dict[str, Any]] = []
            for ann in annotations or []:
                for item in ann.get("result", []) or []:
                    if isinstance(item, dict):
                        res.append(item)
            for pred in predictions or []:
                for item in pred.get("result", []) or []:
                    if isinstance(item, dict):
                        res.append(item)
            return res

        results = iter_results()
        if not results:
            return []

        normalized: List[Dict[str, Any]] = []

        for r in results:
            r_type = r.get("type")
            from_name = r.get("from_name") or r.get("fromName")
            value_obj = r.get("value") or {}
            if not isinstance(value_obj, dict):
                continue

            # 将 Label Studio 的 value 映射为 values，方便前端统一解析
            values: Dict[str, Any] = {}
            for key, v in value_obj.items():
                values[key] = v

            tag = {
                "id": r.get("id"),
                "type": r_type,
                "from_name": from_name,
                "values": values,
            }
            normalized.append(tag)

        return normalized
