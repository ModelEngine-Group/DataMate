"""数据合成服务 - 核心业务逻辑层"""
import asyncio
from contextlib import asynccontextmanager

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models.base_entity import LineageNode, LineageEdge
from app.db.models.data_synthesis import (
    DataSynthInstance,
    DataSynthesisFileInstance,
    DataSynthesisChunkInstance,
    SynthesisData,
)
from app.db.models.dataset_management import DatasetFiles, Dataset
from app.db.session import logger, AsyncSessionLocal
from app.module.generation.schema.generation import Config, SyntheConfig
from app.module.generation.service.chunk_processor import ChunkProcessor
from app.module.generation.service.qa_generator import QAGenerator
from app.module.generation.service.qa_generator import _filter_docs_by_size
from app.module.generation.service.task_executor import run_in_thread
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

    @asynccontextmanager
    async def _session_scope(self):
        """
        创建独立的数据库会话上下文管理器
        用于长时间运行的任务，避免长时间占用连接
        """
        session = AsyncSessionLocal()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    def _load_and_split_sync(
        self, file_path: str, chunk_size: int, chunk_overlap: int
    ):
        """
        同步方法：加载并切分文件
        在线程池中执行，不阻塞事件循环
        """
        try:
            docs = load_documents(file_path)
            split_docs = DocumentSplitter.auto_split(docs, chunk_size, chunk_overlap)
            return _filter_docs_by_size(split_docs, chunk_size)
        except Exception as e:
            logger.error(f"Error loading or splitting file {file_path}: {e}")
            raise

    async def process_task(self, task_id: str):
        """
        处理数据合成任务入口 - 使用独立会话和线程池

        Args:
            task_id: 合成任务ID
        """
        # 使用独立的数据库会话，不与API请求共享
        async with self._session_scope() as session:
            synth_task: DataSynthInstance | None = await session.get(
                DataSynthInstance, task_id
            )
            if not synth_task:
                logger.error(f"Synthesis task {task_id} not found, abort processing")
                return

            logger.info(f"Start processing synthesis task {task_id}")

            # 更新任务状态为处理中
            synth_task.status = "processing"
            await session.commit()

            # 从 synth_config 中读取 max_qa_pairs
            max_qa_pairs = self._parse_max_qa_pairs(synth_task)

            # 获取任务关联的文件ID列表
            file_ids = await self._get_file_ids_for_task(session, task_id)
            if not file_ids:
                logger.warning(
                    f"No files associated with task {task_id}, abort processing"
                )
                await self._mark_task_failed(session, task_id, "no_files_associated")
                return

            # 逐个文件处理
            processed_count = 0
            total_task_chunks = 0
            processed_task_chunks = 0
            for file_id in file_ids:
                try:
                    file_task = await self._get_or_create_file_instance(
                        session, str(synth_task.id), file_id
                    )
                    success = await self._process_single_file(
                        session, synth_task, file_id, max_qa_pairs=max_qa_pairs
                    )
                    # 累加任务级别的切片统计
                    if file_task:
                        total_task_chunks += file_task.total_chunks or 0
                        processed_task_chunks += file_task.processed_chunks or 0
                except Exception as e:
                    logger.exception(
                        f"Unexpected error when processing file {file_id} for task {task_id}: {e}"
                    )
                    await self._mark_file_failed(
                        session, str(synth_task.id), file_id, str(e)
                    )
                    success = False

                if success:
                    processed_count += 1
                    synth_task.processed_files = processed_count
                    # 更新任务级别的切片统计
                    synth_task.total_chunks = total_task_chunks
                    synth_task.processed_chunks = processed_task_chunks
                    await session.commit()

            # 更新最终任务状态
            if processed_count == len(file_ids):
                synth_task.status = "completed"
            else:
                synth_task.status = "partially_completed"
            # 确保任务完成时切片统计准确
            if synth_task.status in ("completed", "partially_completed"):
                synth_task.total_chunks = total_task_chunks
                synth_task.processed_chunks = processed_task_chunks
            await session.commit()

            logger.info(f"Finished processing synthesis task {synth_task.id}")

    def _parse_max_qa_pairs(self, synth_task: DataSynthInstance) -> int | None:
        """解析最大QA对数量配置"""
        try:
            cfg = Config(**(synth_task.synth_config or {}))
            max_qa_pairs = (
                cfg.max_qa_pairs
                if (cfg and cfg.max_qa_pairs and cfg.max_qa_pairs > 0)
                else None
            )
        except Exception:
            max_qa_pairs = None
        return max_qa_pairs

    async def _process_single_file(
        self,
        session: AsyncSession,
        synth_task: DataSynthInstance,
        file_id: str,
        max_qa_pairs: int | None = None,
    ) -> bool:
        """
        处理单个源文件 - 使用线程池执行阻塞操作

        Args:
            session: 数据库会话
            synth_task: 合成任务实例
            file_id: 源文件ID
            max_qa_pairs: 最大QA对数量限制

        Returns:
            处理是否成功
        """
        # 解析文件路径
        file_path = await self._resolve_file_path(session, file_id)
        if not file_path:
            logger.warning(f"File path not found for file_id={file_id}, skip")
            await self._mark_file_failed(
                session, str(synth_task.id), file_id, "file_path_not_found"
            )
            return False

        logger.info(f"Processing file_id={file_id}, path={file_path}")

        # 解析配置
        try:
            config = Config(**(synth_task.synth_config or {}))
        except Exception as e:
            logger.error(f"Invalid synth_config for task={synth_task.id}: {e}")
            await self._mark_file_failed(
                session, str(synth_task.id), file_id, "invalid_synth_config"
            )
            return False

        # 1. 加载并切片 - 在线程池中执行阻塞操作
        try:
            chunks = await run_in_thread(
                self._load_and_split_sync,
                file_path,
                config.text_split_config.chunk_size,
                config.text_split_config.chunk_overlap,
            )
        except Exception as e:
            logger.error(f"Failed to load and split file {file_id}: {e}")
            await self._mark_file_failed(
                session, str(synth_task.id), file_id, f"load_split_failed: {e}"
            )
            return False

        if not chunks:
            logger.warning(f"No chunks generated for file_id={file_id}")
            await self._mark_file_failed(
                session, str(synth_task.id), file_id, "no_chunks_generated"
            )
            return False

        logger.info(f"File {file_id} split into {len(chunks)} chunks")

        # 2. 获取文件实例并持久化切片
        file_task = await self._get_or_create_file_instance(
            session,
            synthesis_task_id=str(synth_task.id),
            source_file_id=file_id,
        )
        if not file_task:
            logger.error(
                f"DataSynthesisFileInstance not found for task={synth_task.id}, file_id={file_id}"
            )
            await self._mark_file_failed(
                session, str(synth_task.id), file_id, "file_instance_not_found"
            )
            return False

        # 使用 ChunkProcessor 持久化切片
        chunk_processor = ChunkProcessor(session)
        await chunk_processor.persist_chunks(synth_task, file_task, file_id, chunks)
        total_chunks = len(chunks)
        del chunks  # 释放内存

        # 3. 验证问答配置
        question_cfg: SyntheConfig | None = config.question_synth_config
        answer_cfg: SyntheConfig | None = config.answer_synth_config
        if not question_cfg or not answer_cfg:
            logger.error(
                f"Question/Answer synth config missing for task={synth_task.id}, file={file_id}"
            )
            await self._mark_file_failed(
                session, str(synth_task.id), file_id, "qa_config_missing"
            )
            return False

        logger.info(
            f"Start QA generation for task={synth_task.id}, file={file_id}, total_chunks={total_chunks}"
        )

        # 4. 创建模型客户端
        question_model = await get_model_by_id(session, question_cfg.model_id)
        answer_model = await get_model_by_id(session, answer_cfg.model_id)
        question_chat = LLMFactory.create_chat(
            question_model.model_name, question_model.base_url, question_model.api_key
        )
        answer_chat = LLMFactory.create_chat(
            answer_model.model_name, answer_model.base_url, answer_model.api_key
        )

        # 5. 分批次处理切片
        await self._process_chunks_in_batches(
            session=session,
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
        await session.commit()
        await session.refresh(file_task)
        return True

    async def _process_chunks_in_batches(
        self,
        session: AsyncSession,
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
            session: 数据库会话
            file_task: 文件任务实例
            total_chunks: 总切片数
            question_cfg: 问题生成配置
            answer_cfg: 答案生成配置
            question_chat: 问题生成模型
            answer_chat: 答案生成模型
            synth_task_id: 合成任务ID
            max_qa_pairs: 最大QA对数量限制
        """
        batch_size = 50  # 减小批次大小，降低内存占用
        current_index = 1

        chunk_processor = ChunkProcessor(session)
        qa_generator = QAGenerator(session)

        while current_index <= total_chunks:
            end_index = min(current_index + batch_size - 1, total_chunks)

            # 使用 ChunkProcessor 加载切片批次
            chunk_batch = await chunk_processor.load_chunk_batch(
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

            # 顺序处理每个切片，避免并发过高
            for chunk in chunk_batch:
                try:
                    success = await self._process_single_chunk(
                        session=session,
                        file_task=file_task,
                        chunk=chunk,
                        question_cfg=question_cfg,
                        answer_cfg=answer_cfg,
                        question_chat=question_chat,
                        answer_chat=answer_chat,
                        synth_task_id=synth_task_id,
                        max_qa_pairs=max_qa_pairs,
                        qa_generator=qa_generator,
                    )
                    if success:
                        # 更新已处理的切片计数
                        file_task.processed_chunks = (file_task.processed_chunks or 0) + 1
                        # 实时刷新进度到数据库
                        await session.commit()
                        await session.refresh(file_task)
                        logger.info(f"File {file_task.id} progress: {file_task.processed_chunks}/{file_task.total_chunks} chunks processed")
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk.id}: {e}")
                    # 即使处理失败，也要更新进度
                    file_task.processed_chunks = (file_task.processed_chunks or 0) + 1
                    await session.commit()
                    await session.refresh(file_task)

                # 短暂释放控制权，让出事件循环，处理其他请求
                await asyncio.sleep(0)

            current_index = end_index + 1

    async def _process_single_chunk(
        self,
        session: AsyncSession,
        file_task: DataSynthesisFileInstance,
        chunk: DataSynthesisChunkInstance,
        question_cfg: SyntheConfig,
        answer_cfg: SyntheConfig,
        question_chat,
        answer_chat,
        synth_task_id: str,
        max_qa_pairs: int | None,
        qa_generator: QAGenerator,
    ) -> bool:
        """处理单个切片

        Args:
            session: 数据库会话
            file_task: 文件任务实例
            chunk: 切片实例
            question_cfg: 问题生成配置
            answer_cfg: 答案生成配置
            question_chat: 问题生成模型
            answer_chat: 答案生成模型
            synth_task_id: 合成任务ID
            max_qa_pairs: 最大QA对数量限制
            qa_generator: QA生成器

        Returns:
            处理是否成功
        """
        # 检查QA对数量上限
        if max_qa_pairs and max_qa_pairs > 0:
            if await qa_generator.check_qa_limit(synth_task_id, max_qa_pairs):
                logger.info(f"max_qa_pairs reached, skipping chunk {chunk.chunk_index}")
                file_task.status = "completed"
                if file_task.total_chunks is not None:
                    file_task.processed_chunks = file_task.total_chunks
                await session.commit()
                await session.refresh(file_task)
                return False

        # 使用 QAGenerator 处理问答生成
        success_count = await qa_generator.process_chunk_qa(
            file_task=file_task,
            chunk=chunk,
            question_cfg=question_cfg,
            answer_cfg=answer_cfg,
            question_chat=question_chat,
            answer_chat=answer_chat,
        )

        return success_count > 0

    async def _resolve_file_path(self, session: AsyncSession, file_id: str) -> str | None:
        """根据文件ID获取文件路径

        Args:
            session: 数据库会话
            file_id: 文件ID

        Returns:
            文件路径
        """
        result = await session.execute(
            select(DatasetFiles).where(DatasetFiles.id == file_id)
        )
        file_obj = result.scalar_one_or_none()
        if not file_obj:
            return None
        return file_obj.file_path

    async def _get_or_create_file_instance(
        self,
        session: AsyncSession,
        synthesis_task_id: str,
        source_file_id: str,
    ) -> DataSynthesisFileInstance | None:
        """获取或创建文件任务实例

        Args:
            session: 数据库会话
            synthesis_task_id: 合成任务ID
            source_file_id: 源文件ID

        Returns:
            文件任务实例
        """
        result = await session.execute(
            select(DataSynthesisFileInstance).where(
                DataSynthesisFileInstance.synthesis_instance_id == synthesis_task_id,
                DataSynthesisFileInstance.source_file_id == source_file_id,
            )
        )
        return result.scalar_one_or_none()

    async def _mark_file_failed(
        self,
        session: AsyncSession,
        synth_task_id: str,
        file_id: str,
        reason: str | None = None,
    ) -> None:
        """标记文件任务失败

        Args:
            session: 数据库会话
            synth_task_id: 合成任务ID
            file_id: 文件ID
            reason: 失败原因
        """
        try:
            result = await session.execute(
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
            await session.commit()
            await session.refresh(file_task)
            logger.info(
                f"Marked file task as failed for task={synth_task_id}, file_id={file_id}, reason={reason}"
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error when marking file failed for task={synth_task_id}, file_id={file_id}, original_reason={reason}, error={e}"
            )

    async def _get_file_ids_for_task(
        self, session: AsyncSession, synth_task_id: str
    ):
        """获取任务关联的文件ID列表

        Args:
            session: 数据库会话
            synth_task_id: 合成任务ID

        Returns:
            文件ID列表
        """
        result = await session.execute(
            select(DataSynthesisFileInstance.source_file_id).where(
                DataSynthesisFileInstance.synthesis_instance_id == synth_task_id
            )
        )
        return result.scalars().all()

    async def _mark_task_failed(
        self,
        session: AsyncSession,
        task_id: str,
        reason: str | None = None,
    ) -> None:
        """标记任务失败

        Args:
            session: 数据库会话
            task_id: 任务ID
            reason: 失败原因
        """
        try:
            task = await session.get(DataSynthInstance, task_id)
            if task:
                task.status = "failed"
                await session.commit()
                logger.info(
                    f"Marked task {task_id} as failed, reason={reason}"
                )
        except Exception as e:
            logger.exception(f"Error marking task {task_id} as failed: {e}")

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
            task = await db.get(DataSynthInstance, task_id)
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
            src_dataset = await db.get(Dataset, src_dataset_id)
            dst_dataset = await db.get(Dataset, dest_dataset_id)

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
            await db.commit()

            logger.info(f"Added synthesis lineage: {src_node.name} -> {dest_dataset.name}")
        except Exception as exc:
            logger.error(f"Failed to add synthesis lineage: {exc}")
