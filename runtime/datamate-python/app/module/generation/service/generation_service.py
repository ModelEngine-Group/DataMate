"""数据合成服务 - 核心业务逻辑层"""
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.base_entity import LineageNode, LineageEdge
from app.db.models.data_synthesis import (
    DataSynthInstance,
    DataSynthesisFileInstance,
    DataSynthesisChunkInstance,
    SynthesisData,
)
from app.db.models.dataset_management import DatasetFiles, Dataset
from app.db.session import logger
from app.module.generation.schema.generation import Config, SyntheConfig
from app.module.generation.service.chunk_processor import ChunkProcessor
from app.module.generation.service.qa_generator import QAGenerator
from app.module.generation.service.qa_generator import _filter_docs_by_size
from app.module.shared.common.document_loaders import load_documents
from app.module.shared.common.text_split import DocumentSplitter
from app.module.shared.llm import LLMFactory
from app.module.system.service.common_service import get_model_by_id
from app.module.shared.common.lineage import LineageService
from app.module.shared.schema import NodeType, EdgeType


class GenerationService:
    """数据合成服务 - 使用模块化架构"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.chunk_processor = ChunkProcessor(db)
        self.qa_generator = QAGenerator(db)

    async def process_task(self, task_id: str):
        """处理数据合成任务入口

        Args:
            task_id: 合成任务ID
        """
        synth_task: DataSynthInstance | None = await self.db.get(DataSynthInstance, task_id)
        if not synth_task:
            logger.error(f"Synthesis task {task_id} not found, abort processing")
            return

        logger.info(f"Start processing synthesis task {task_id}")

        # 从 synth_config 中读取 max_qa_pairs
        max_qa_pairs = self._parse_max_qa_pairs(synth_task)

        # 获取任务关联的文件ID列表
        file_ids = await self._get_file_ids_for_task(task_id)
        if not file_ids:
            logger.warning(f"No files associated with task {task_id}, abort processing")
            return

        # 逐个文件处理
        for file_id in file_ids:
            try:
                success = await self._process_single_file(
                    synth_task, file_id, max_qa_pairs=max_qa_pairs
                )
            except Exception as e:
                logger.exception(
                    f"Unexpected error when processing file {file_id} for task {task_id}: {e}"
                )
                await self._mark_file_failed(str(synth_task.id), file_id, str(e))
                success = False

            if success:
                synth_task.processed_files = (synth_task.processed_files or 0) + 1
                await self.db.commit()
                await self.db.refresh(synth_task)

        logger.info(f"Finished processing synthesis task {synth_task.id}")

    def _parse_max_qa_pairs(self, synth_task: DataSynthInstance) -> int | None:
        """解析最大QA对数量配置"""
        try:
            cfg = Config(**(synth_task.synth_config or {}))
            max_qa_pairs = cfg.max_qa_pairs if (cfg and cfg.max_qa_pairs and cfg.max_qa_pairs > 0) else None
        except Exception:
            max_qa_pairs = None
        return max_qa_pairs

    async def _process_single_file(
        self,
        synth_task: DataSynthInstance,
        file_id: str,
        max_qa_pairs: int | None = None,
    ) -> bool:
        """处理单个源文件

        Args:
            synth_task: 合成任务实例
            file_id: 源文件ID
            max_qa_pairs: 最大QA对数量限制

        Returns:
            处理是否成功
        """
        # 解析文件路径
        file_path = await self._resolve_file_path(file_id)
        if not file_path:
            logger.warning(f"File path not found for file_id={file_id}, skip")
            await self._mark_file_failed(str(synth_task.id), file_id, "file_path_not_found")
            return False

        logger.info(f"Processing file_id={file_id}, path={file_path}")

        # 解析配置
        try:
            config = Config(**(synth_task.synth_config or {}))
        except Exception as e:
            logger.error(f"Invalid synth_config for task={synth_task.id}: {e}")
            await self._mark_file_failed(str(synth_task.id), file_id, "invalid_synth_config")
            return False

        # 1. 加载并切片
        chunks = self._load_and_split(
            file_path,
            config.text_split_config.chunk_size,
            config.text_split_config.chunk_overlap,
        )
        if not chunks:
            logger.warning(f"No chunks generated for file_id={file_id}")
            await self._mark_file_failed(str(synth_task.id), file_id, "no_chunks_generated")
            return False

        logger.info(f"File {file_id} split into {len(chunks)} chunks")

        # 2. 获取文件实例并持久化切片
        file_task = await self._get_or_create_file_instance(
            synthesis_task_id=str(synth_task.id),
            source_file_id=file_id,
        )
        if not file_task:
            logger.error(f"DataSynthesisFileInstance not found for task={synth_task.id}, file_id={file_id}")
            await self._mark_file_failed(str(synth_task.id), file_id, "file_instance_not_found")
            return False

        # 使用 ChunkProcessor 持久化切片
        await self.chunk_processor.persist_chunks(synth_task, file_task, file_id, chunks)
        total_chunks = len(chunks)
        del chunks

        # 3. 验证问答配置
        question_cfg: SyntheConfig | None = config.question_synth_config
        answer_cfg: SyntheConfig | None = config.answer_synth_config
        if not question_cfg or not answer_cfg:
            logger.error(f"Question/Answer synth config missing for task={synth_task.id}, file={file_id}")
            await self._mark_file_failed(str(synth_task.id), file_id, "qa_config_missing")
            return False

        logger.info(f"Start QA generation for task={synth_task.id}, file={file_id}, total_chunks={total_chunks}")

        # 4. 创建模型客户端
        question_model = await get_model_by_id(self.db, question_cfg.model_id)
        answer_model = await get_model_by_id(self.db, answer_cfg.model_id)
        question_chat = LLMFactory.create_chat(
            question_model.model_name, question_model.base_url, question_model.api_key
        )
        answer_chat = LLMFactory.create_chat(
            answer_model.model_name, answer_model.base_url, answer_model.api_key
        )

        # 5. 分批次处理切片
        await self._process_chunks_in_batches(
            file_task=file_task,
            total_chunks=total_chunks,
            question_cfg=question_cfg,
            answer_cfg=answer_cfg,
            question_chat=question_chat,
            answer_chat=answer_chat,
            synth_task_id=str(synth_task.id),
            max_qa_pairs=max_qa_pairs,
        )

        # 6. 标记文件任务完成
        file_task.status = "completed"
        await self.db.commit()
        await self.db.refresh(file_task)
        return True

    async def _process_chunks_in_batches(
        self,
        file_task: DataSynthesisFileInstance,
        total_chunks: int,
        question_cfg: SyntheConfig,
        answer_cfg: SyntheConfig,
        question_chat,
        answer_chat,
        synth_task_id: str,
        max_qa_pairs: int | None,
    ) -> None:
        """分批次处理切片

        Args:
            file_task: 文件任务实例
            total_chunks: 总切片数
            question_cfg: 问题生成配置
            answer_cfg: 答案生成配置
            question_chat: 问题生成模型
            answer_chat: 答案生成模型
            synth_task_id: 合成任务ID
            max_qa_pairs: 最大QA对数量限制
        """
        batch_size = 100
        current_index = 1

        while current_index <= total_chunks:
            end_index = min(current_index + batch_size - 1, total_chunks)

            # 使用 ChunkProcessor 加载切片批次
            chunk_batch = await self.chunk_processor.load_chunk_batch(
                file_task_id=file_task.id,
                start_index=current_index,
                end_index=end_index,
            )

            if not chunk_batch:
                logger.warning(
                    f"Empty chunk batch loaded for file={file_task.id}, range=[{current_index}, {end_index}]"
                )
                current_index = end_index + 1
                continue

            # 并发处理每个切片
            tasks = [
                self._process_single_chunk(
                    file_task=file_task,
                    chunk=chunk,
                    question_cfg=question_cfg,
                    answer_cfg=answer_cfg,
                    question_chat=question_chat,
                    answer_chat=answer_chat,
                    synth_task_id=synth_task_id,
                    max_qa_pairs=max_qa_pairs,
                )
                for chunk in chunk_batch
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

            current_index = end_index + 1

    async def _process_single_chunk(
        self,
        file_task: DataSynthesisFileInstance,
        chunk: DataSynthesisChunkInstance,
        question_cfg: SyntheConfig,
        answer_cfg: SyntheConfig,
        question_chat,
        answer_chat,
        synth_task_id: str,
        max_qa_pairs: int | None,
    ) -> bool:
        """处理单个切片

        Args:
            file_task: 文件任务实例
            chunk: 切片实例
            question_cfg: 问题生成配置
            answer_cfg: 答案生成配置
            question_chat: 问题生成模型
            answer_chat: 答案生成模型
            synth_task_id: 合成任务ID
            max_qa_pairs: 最大QA对数量限制

        Returns:
            处理是否成功
        """
        # 检查QA对数量上限
        if max_qa_pairs and max_qa_pairs > 0:
            if await self.qa_generator.check_qa_limit(synth_task_id, max_qa_pairs):
                logger.info(f"max_qa_pairs reached, skipping chunk {chunk.chunk_index}")
                file_task.status = "completed"
                if file_task.total_chunks is not None:
                    file_task.processed_chunks = file_task.total_chunks
                await self.db.commit()
                await self.db.refresh(file_task)
                return False

        # 使用 QAGenerator 处理问答生成
        success_count = await self.qa_generator.process_chunk_qa(
            file_task=file_task,
            chunk=chunk,
            question_cfg=question_cfg,
            answer_cfg=answer_cfg,
            question_chat=question_chat,
            answer_chat=answer_chat,
        )

        # 更新已处理切片计数
        await self._increment_processed_chunks(file_task.id, 1)

        return success_count > 0

    def _load_and_split(self, file_path: str, chunk_size: int, chunk_overlap: int):
        """加载并切分文件

        Args:
            file_path: 文件路径
            chunk_size: 切片大小
            chunk_overlap: 切片重叠大小

        Returns:
            切片列表
        """
        try:
            docs = load_documents(file_path)
            split_docs = DocumentSplitter.auto_split(docs, chunk_size, chunk_overlap)
            return _filter_docs_by_size(split_docs, chunk_size)
        except Exception as e:
            logger.error(f"Error loading or splitting file {file_path}: {e}")
            raise

    async def _resolve_file_path(self, file_id: str) -> str | None:
        """根据文件ID获取文件路径

        Args:
            file_id: 文件ID

        Returns:
            文件路径
        """
        result = await self.db.execute(
            select(DatasetFiles).where(DatasetFiles.id == file_id)
        )
        file_obj = result.scalar_one_or_none()
        if not file_obj:
            return None
        return file_obj.file_path

    async def _get_or_create_file_instance(
        self,
        synthesis_task_id: str,
        source_file_id: str,
    ) -> DataSynthesisFileInstance | None:
        """获取或创建文件任务实例

        Args:
            synthesis_task_id: 合成任务ID
            source_file_id: 源文件ID

        Returns:
            文件任务实例
        """
        result = await self.db.execute(
            select(DataSynthesisFileInstance).where(
                DataSynthesisFileInstance.synthesis_instance_id == synthesis_task_id,
                DataSynthesisFileInstance.source_file_id == source_file_id,
            )
        )
        return result.scalar_one_or_none()

    async def _mark_file_failed(
        self, synth_task_id: str, file_id: str, reason: str | None = None
    ) -> None:
        """标记文件任务失败

        Args:
            synth_task_id: 合成任务ID
            file_id: 文件ID
            reason: 失败原因
        """
        try:
            result = await self.db.execute(
                select(DataSynthesisFileInstance).where(
                    DataSynthesisFileInstance.synthesis_instance_id == synth_task_id,
                    DataSynthesisFileInstance.source_file_id == file_id,
                )
            )
            file_task = result.scalar_one_or_none()
            if not file_task:
                logger.warning(
                    f"Failed to mark file as failed: no DataSynthesisFileInstance found for task={synth_task_id}, file_id={file_id}, reason={reason}"
                )
                return

            file_task.status = "failed"
            await self.db.commit()
            await self.db.refresh(file_task)
            logger.info(f"Marked file task as failed for task={synth_task_id}, file_id={file_id}, reason={reason}")
        except Exception as e:
            logger.exception(
                f"Unexpected error when marking file failed for task={synth_task_id}, file_id={file_id}, original_reason={reason}, error={e}"
            )

    async def _get_file_ids_for_task(self, synth_task_id: str):
        """获取任务关联的文件ID列表

        Args:
            synth_task_id: 合成任务ID

        Returns:
            文件ID列表
        """
        result = await self.db.execute(
            select(DataSynthesisFileInstance.source_file_id)
            .where(DataSynthesisFileInstance.synthesis_instance_id == synth_task_id)
        )
        return result.scalars().all()

    async def _increment_processed_chunks(self, file_task_id: str, delta: int) -> None:
        """增加已处理切片计数

        Args:
            file_task_id: 文件任务ID
            delta: 增量
        """
        result = await self.db.execute(
            select(DataSynthesisFileInstance).where(
                DataSynthesisFileInstance.id == file_task_id,
            )
        )
        file_task = result.scalar_one_or_none()
        if not file_task:
            logger.error(f"Failed to increment processed_chunks: file_task {file_task_id} not found")
            return

        new_value = (file_task.processed_chunks or 0) + int(delta)
        total = file_task.total_chunks
        if isinstance(total, int) and total >= 0:
            new_value = min(new_value, total)

        file_task.processed_chunks = new_value
        await self.db.commit()
        await self.db.refresh(file_task)

    async def add_synthesis_to_graph(
        self, db: AsyncSession, task_id: str, dest_dataset_id: str
    ) -> None:
        """记录数据合成血缘关系

        Args:
            db: 数据库会话
            task_id: 任务ID
            dest_dataset_id: 目标数据集ID
        """
        try:
            task = await self.db.get(DataSynthInstance, task_id)
            src_dataset_result = await db.execute(
                select(DatasetFiles.dataset_id)
                .join(
                    DataSynthesisFileInstance,
                    DatasetFiles.id == DataSynthesisFileInstance.source_file_id,
                )
                .where(DataSynthesisFileInstance.synthesis_instance_id == task_id)
                .limit(1)
            )
            src_dataset_id = src_dataset_result.scalar_one_or_none()
            src_dataset = await self.db.get(Dataset, src_dataset_id)
            dst_dataset = await self.db.get(Dataset, dest_dataset_id)

            if not task or not dst_dataset:
                logger.warning("Missing task or destination dataset for lineage graph")
                return

            src_node = LineageNode(
                id=src_dataset.id,
                node_type=NodeType.DATASET.value,
                name=src_dataset.name,
                description=src_dataset.description,
            )
            dest_node = LineageNode(
                id=dst_dataset.id,
                node_type=NodeType.DATASET.value,
                name=dst_dataset.name,
                description=dst_dataset.description,
            )
            synthesis_edge = LineageEdge(
                process_id=task_id,
                name=task.name,
                edge_type=EdgeType.DATA_SYNTHESIS.value,
                description=task.description,
                from_node_id=src_node.id,
                to_node_id=dst_dataset.id,
            )

            lineage_service = LineageService(db=db)
            await lineage_service.generate_graph(src_node, synthesis_edge, dest_node)
            await self.db.commit()

            logger.info(f"Added synthesis lineage: {src_node.name} -> {dest_dataset.name}")
        except Exception as exc:
            logger.error(f"Failed to add synthesis lineage: {exc}")
