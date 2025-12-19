import asyncio
import json
import uuid

from langchain_core.language_models import BaseChatModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.data_synthesis import (
    DataSynthInstance,
    DataSynthesisFileInstance,
    DataSynthesisChunkInstance,
    SynthesisData,
)
from app.db.models.dataset_management import DatasetFiles
from app.db.session import logger
from app.module.generation.schema.generation import Config, SyntheConfig
from app.module.generation.service.prompt import (
    QUESTION_GENERATOR_PROMPT,
    ANSWER_GENERATOR_PROMPT,
)
from app.module.shared.common.document_loaders import load_documents
from app.module.shared.common.text_split import DocumentSplitter
from app.module.shared.util.model_chat import extract_json_substring
from app.module.system.service.common_service import chat, get_model_by_id, get_chat_client


def _filter_docs(split_docs, chunk_size):
    """
    过滤文档，移除长度小于 chunk_size 的文档
    """
    filtered_docs = []
    for doc in split_docs:
        if len(doc.page_content) >= chunk_size * 0.7:
            filtered_docs.append(doc)
    return filtered_docs


class GenerationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # 全局并发信号量：保证任意时刻最多 10 次模型调用
        self.question_semaphore = asyncio.Semaphore(10)
        self.answer_semaphore = asyncio.Semaphore(100)

    async def process_task(self, task_id: str):
        """处理数据合成任务入口：根据任务ID加载任务并逐个处理源文件。"""
        synth_task: DataSynthInstance | None = await self.db.get(DataSynthInstance, task_id)
        if not synth_task:
            logger.error(f"Synthesis task {task_id} not found, abort processing")
            return

        logger.info(f"Start processing synthe task {task_id}")

        # 从 synth_config 中读取 max_qa_pairs，全局控制 QA 总量上限；<=0 或异常则视为不限制
        try:
            cfg = Config(**(synth_task.synth_config or {}))
            max_qa_pairs = cfg.max_qa_pairs if (cfg and cfg.max_qa_pairs and cfg.max_qa_pairs > 0) else None
        except Exception:
            max_qa_pairs = None

        # 获取任务关联的文件原始ID列表
        file_ids = await self._get_file_ids_for_task(task_id)
        if not file_ids:
            logger.warning(f"No files associated with task {task_id}, abort processing")
            return

        # 逐个文件处理
        for file_id in file_ids:
            try:
                success = await self._process_single_file(synth_task, file_id, max_qa_pairs=max_qa_pairs)
            except Exception as e:
                logger.exception(f"Unexpected error when processing file {file_id} for task {task_id}: {e}")
                # 确保对应文件任务状态标记为失败
                await self._mark_file_failed(str(synth_task.id), file_id, str(e))
                success = False

            if success:
                # 每处理完一个文件，简单增加 processed_files 计数
                synth_task.processed_files = (synth_task.processed_files or 0) + 1
                await self.db.commit()
                await self.db.refresh(synth_task)

        logger.info(f"Finished processing synthesis task {synth_task.id}")

    # ==================== 高层文件处理流程 ====================
    async def _process_single_file(
        self,
        synth_task: DataSynthInstance,
        file_id: str,
        max_qa_pairs: int | None = None,
    ) -> bool:
        """按 chunk 批量流式处理单个源文件。

        流程：
        1. 切片并将所有 chunk 持久化到 DB 后释放内存；
        2. 从 DB 按 chunk_index 升序批量读取 chunk；
        3. 对批次中的每个 chunk：先生成指定数量的问题，再基于这些问题生成答案；
        4. 每成功处理完一个 chunk（即该 chunk 至少生成一条 QA）就更新一次 processed_chunks；
        5. 全部完成后将文件实例标记为 completed。
        """
        # 解析文件路径与配置
        file_path = await self._resolve_file_path(file_id)
        if not file_path:
            logger.warning(f"File path not found for file_id={file_id}, skip")
            await self._mark_file_failed(str(synth_task.id), file_id, "file_path_not_found")
            return False

        logger.info(f"Processing file_id={file_id}, path={file_path}")

        try:
            config = Config(**(synth_task.synth_config or {}))
        except Exception as e:
            logger.error(f"Invalid synth_config for task={synth_task.id}: {e}")
            await self._mark_file_failed(str(synth_task.id), file_id, "invalid_synth_config")
            return False

        # 1. 加载并切片（仅在此处占用内存）
        chunks = self._load_and_split(
            file_path,
            config.text_split_config.chunk_size,
            config.text_split_config.chunk_overlap,
        )
        if not chunks:
            logger.warning(f"No chunks generated for file_id={file_id}")
            await self._mark_file_failed(str(synth_task.id), file_id, "no_chunks_generated")
            return False

        logger.info(f"File {file_id} split into {len(chunks)} chunks by LangChain")

        # 2. 获取文件实例并持久化 chunk 记录
        file_task = await self._get_or_create_file_instance(
            synthesis_task_id=str(synth_task.id),
            source_file_id=file_id,
        )
        if not file_task:
            logger.error(
                f"DataSynthesisFileInstance not found for task={synth_task.id}, file_id={file_id}"
            )
            await self._mark_file_failed(str(synth_task.id), file_id, "file_instance_not_found")
            return False

        await self._persist_chunks(synth_task, file_task, file_id, chunks)
        total_chunks = len(chunks)
        # 释放内存中的切片
        del chunks

        # 3. 读取问答配置
        question_cfg: SyntheConfig | None = config.question_synth_config
        answer_cfg: SyntheConfig | None = config.answer_synth_config
        if not question_cfg or not answer_cfg:
            logger.error(
                f"Question/Answer synth config missing for task={synth_task.id}, file={file_id}"
            )
            await self._mark_file_failed(str(synth_task.id), file_id, "qa_config_missing")
            return False

        logger.info(
            f"Start QA generation for task={synth_task.id}, file={file_id}, total_chunks={total_chunks}"
        )

        # 为本文件构建模型 client
        question_model = await get_model_by_id(self.db, question_cfg.model_id)
        answer_model = await get_model_by_id(self.db, answer_cfg.model_id)
        question_chat = get_chat_client(question_model)
        answer_chat = get_chat_client(answer_model)

        # 分批次从 DB 读取并处理 chunk
        batch_size = 20
        current_index = 1

        while current_index <= total_chunks:
            end_index = min(current_index + batch_size - 1, total_chunks)
            chunk_batch = await self._load_chunk_batch(
                file_task_id=file_task.id,
                start_index=current_index,
                end_index=end_index,
            )
            if not chunk_batch:
                logger.warning(
                    f"Empty chunk batch loaded for file={file_id}, range=[{current_index}, {end_index}]"
                )
                current_index = end_index + 1
                continue

            # 对本批中的每个 chunk 并发处理（内部受 semaphore 限流）
            async def process_one(chunk: DataSynthesisChunkInstance) -> bool:
                return await self._process_single_chunk_qa(
                    file_task=file_task,
                    chunk=chunk,
                    question_cfg=question_cfg,
                    answer_cfg=answer_cfg,
                    question_chat=question_chat,
                    answer_chat=answer_chat,
                    synth_task_id=str(synth_task.id),
                    max_qa_pairs=max_qa_pairs,
                )

            tasks = [process_one(chunk) for chunk in chunk_batch]
            await asyncio.gather(*tasks, return_exceptions=True)

            current_index = end_index + 1

        # 全部完成
        file_task.status = "completed"
        await self.db.commit()
        await self.db.refresh(file_task)
        return True

    async def _process_single_chunk_qa(
        self,
        file_task: DataSynthesisFileInstance,
        chunk: DataSynthesisChunkInstance,
        question_cfg: SyntheConfig,
        answer_cfg: SyntheConfig,
        question_chat: BaseChatModel,
        answer_chat: BaseChatModel,
        synth_task_id: str,
        max_qa_pairs: int | None = None,
    ) -> bool:
        """处理单个 chunk：生成问题列表，然后为每个问题生成答案并落库。

        为了全局控制 QA 总量：在本方法开始处，根据 synth_task_id 查询当前已落盘的
        SynthesisData 条数，如果 >= max_qa_pairs，则不再对当前 chunk 做任何 QA 生成，
        并将当前文件任务标记为 completed，processed_chunks = total_chunks。

        已经进入后续流程的任务（例如其它协程正在生成答案）允许自然执行完。
        """
        # 如果没有全局上限配置，维持原有行为
        if max_qa_pairs is not None and max_qa_pairs > 0:
            from sqlalchemy import func

            # 统计当前整个任务下已生成的 QA 总数
            result = await self.db.execute(
                select(func.count(SynthesisData.id)).where(
                    SynthesisData.synthesis_file_instance_id.in_(
                        select(DataSynthesisFileInstance.id).where(
                            DataSynthesisFileInstance.synthesis_instance_id == synth_task_id
                        )
                    )
                )
            )
            current_qa_count = int(result.scalar() or 0)

            if current_qa_count >= max_qa_pairs:
                logger.info(
                    "max_qa_pairs reached: current=%s, max=%s, task_id=%s, file_task_id=%s, skip new QA generation for this chunk.",
                    current_qa_count,
                    max_qa_pairs,
                    synth_task_id,
                    file_task.id,
                )
                # 将文件任务标记为已完成，并认为所有 chunk 均已处理
                file_task.status = "completed"
                if file_task.total_chunks is not None:
                    file_task.processed_chunks = file_task.total_chunks
                await self.db.commit()
                await self.db.refresh(file_task)
                return False

        # ---- 下面保持原有逻辑不变 ----
        chunk_index = chunk.chunk_index
        chunk_text = chunk.chunk_content or ""
        if not chunk_text.strip():
            logger.warning(
                f"Empty chunk text for file_task={file_task.id}, chunk_index={chunk_index}"
            )
            # 无论成功或失败，均视为该 chunk 已处理完成
            try:
                await self._increment_processed_chunks(file_task.id, 1)
            except Exception as e:
                logger.exception(
                    f"Failed to increment processed_chunks for file_task={file_task.id}, chunk_index={chunk_index}: {e}"
                )
            return False

        success_any = False

        # 1. 生成问题
        try:
            questions = await self._generate_questions_for_one_chunk(
                chunk_text=chunk_text,
                question_cfg=question_cfg,
                question_chat=question_chat,
            )
        except Exception as e:
            logger.error(
                f"Generate questions failed for file_task={file_task.id}, chunk_index={chunk_index}: {e}"
            )
            questions = []

        if not questions:
            logger.info(
                f"No questions generated for file_task={file_task.id}, chunk_index={chunk_index}"
            )
        else:
            # 2. 针对每个问题生成答案并入库
            qa_success = await self._generate_answers_for_one_chunk(
                file_task=file_task,
                chunk=chunk,
                questions=questions,
                answer_cfg=answer_cfg,
                answer_chat=answer_chat,
            )
            success_any = bool(qa_success)

        # 无论本 chunk 处理是否成功，都增加 processed_chunks 计数，避免任务长时间卡住
        try:
            await self._increment_processed_chunks(file_task.id, 1)
        except Exception as e:
            logger.exception(
                f"Failed to increment processed_chunks for file_task={file_task.id}, chunk_index={chunk_index}: {e}"
            )

        return success_any

    async def _generate_questions_for_one_chunk(
        self,
        chunk_text: str,
        question_cfg: SyntheConfig,
        question_chat: BaseChatModel,
    ) -> list[str]:
        """针对单个 chunk 文本，调用 question_chat 生成问题列表。"""
        number = question_cfg.number or 5
        number = number if number is not None else 5
        number = max(int(len(chunk_text) / 1000 * number), 1)
        template = getattr(question_cfg, "prompt_template", QUESTION_GENERATOR_PROMPT)
        template = template if (template is not None and template.strip() != "") else QUESTION_GENERATOR_PROMPT

        prompt = (
            template
            .replace("{text}", chunk_text)
            .replace("{number}", str(number))
            .replace("{textLength}", str(len(chunk_text)))
        )

        async with self.question_semaphore:
            loop = asyncio.get_running_loop()
            raw_answer = await loop.run_in_executor(
                None,
                chat,
                question_chat,
                prompt,
            )

        # 解析为问题列表
        questions = self._parse_questions_from_answer(
            raw_answer,
        )
        return questions

    async def _generate_answers_for_one_chunk(
        self,
        file_task: DataSynthesisFileInstance,
        chunk: DataSynthesisChunkInstance,
        questions: list[str],
        answer_cfg: SyntheConfig,
        answer_chat: BaseChatModel,
    ) -> bool:
        """为一个 chunk 的所有问题生成答案并写入 SynthesisData。

        返回：是否至少成功写入一条 QA。
        """
        if not questions:
            return False

        chunk_text = chunk.chunk_content or ""
        template = getattr(answer_cfg, "prompt_template", ANSWER_GENERATOR_PROMPT)
        template = template if (template is not None and template.strip() != "") else ANSWER_GENERATOR_PROMPT
        extra_vars = getattr(answer_cfg, "extra_prompt_vars", {}) or {}

        success_flags: list[bool] = []

        async def process_single_question(question: str):
            prompt = template.replace("{text}", chunk_text).replace("{question}", question)
            for k, v in extra_vars.items():
                prompt.replace(f"{{{{{k}}}}}", str(v))
            else:
                prompt_local = prompt

            async with self.answer_semaphore:
                loop = asyncio.get_running_loop()
                answer = await loop.run_in_executor(
                    None,
                    chat,
                    answer_chat,
                    prompt_local,
                )

            # 默认结构：与 ANSWER_GENERATOR_PROMPT 一致，并补充 instruction 字段
            base_obj: dict[str, object] = {
                "input": chunk_text,
                "output": answer,
            }

            # 如果模型已经按照 ANSWER_GENERATOR_PROMPT 返回了 JSON，则尝试解析并在其上增加 instruction
            parsed_obj: dict[str, object] | None = None
            if isinstance(answer, str):
                cleaned = extract_json_substring(answer)
                try:
                  parsed = json.loads(cleaned)
                  if isinstance(parsed, dict):
                      parsed_obj = parsed
                except Exception:
                  parsed_obj = None

            if parsed_obj is not None:
                parsed_obj["instruction"] = question
                data_obj = parsed_obj
            else:
                base_obj["instruction"] = question
                data_obj = base_obj

            record = SynthesisData(
                id=str(uuid.uuid4()),
                data=data_obj,
                synthesis_file_instance_id=file_task.id,
                chunk_instance_id=chunk.id,
            )
            self.db.add(record)
            success_flags.append(True)

        tasks = [process_single_question(q) for q in questions]
        await asyncio.gather(*tasks, return_exceptions=True)

        if success_flags:
            await self.db.commit()
            return True
        return False

    @staticmethod
    def _parse_questions_from_answer(
        raw_answer: str,
    ) -> list[str]:
        """从大模型返回中解析问题数组。"""
        if not raw_answer:
            return []

        cleaned = extract_json_substring(raw_answer)
        try:
            data = json.loads(cleaned)
        except Exception as e:
            logger.error(
                f"Failed to parse question list JSON for task: {e}. "
            )
            return []

        if isinstance(data, list):
            return [str(q) for q in data if isinstance(q, str) and q.strip()]
        # 容错：如果是单个字符串
        if isinstance(data, str) and data.strip():
            return [data.strip()]
        return []


    # ==================== 原有辅助方法（文件路径/切片/持久化等） ====================
    async def _resolve_file_path(self, file_id: str) -> str | None:
        """根据文件ID查询 t_dm_dataset_files 并返回 file_path（仅 ACTIVE 文件）。"""
        result = await self.db.execute(
            select(DatasetFiles).where(DatasetFiles.id == file_id)
        )
        file_obj = result.scalar_one_or_none()
        if not file_obj:
            return None
        return file_obj.file_path

    @staticmethod
    def _load_and_split(file_path: str, chunk_size: int, chunk_overlap: int):
        """使用 LangChain 加载文本并进行切片，直接返回 Document 列表。
        Args:
            file_path: 待切片的文件路径
            chunk_size: 切片大小
            chunk_overlap: 切片重叠大小
        """
        try:
            docs = load_documents(file_path)
            split_docs = DocumentSplitter.auto_split(docs, chunk_size, chunk_overlap)
            return _filter_docs(split_docs, chunk_size)
        except Exception as e:
            logger.error(f"Error loading or splitting file {file_path}: {e}")
            raise

    async def _persist_chunks(
        self,
        synthesis_task: DataSynthInstance,
        file_task: DataSynthesisFileInstance,
        file_id: str,
        chunks,
    ) -> None:
        """将切片结果保存到 t_data_synthesis_chunk_instances，并更新文件级分块计数。"""
        for idx, doc in enumerate(chunks, start=1):
            # 先复制原始 Document.metadata，再在其上追加任务相关字段，避免覆盖原有元数据
            base_metadata = dict(getattr(doc, "metadata", {}) or {})
            base_metadata.update(
                {
                    "task_id": str(synthesis_task.id),
                    "file_id": file_id
                }
            )

            chunk_record = DataSynthesisChunkInstance(
                id=str(uuid.uuid4()),
                synthesis_file_instance_id=file_task.id,
                chunk_index=idx,
                chunk_content=doc.page_content,
                chunk_metadata=base_metadata,
            )
            self.db.add(chunk_record)

        # 更新文件任务的分块数量
        file_task.total_chunks = len(chunks)
        file_task.status = "processing"

        await self.db.commit()
        await self.db.refresh(file_task)

    async def _get_or_create_file_instance(
        self,
        synthesis_task_id: str,
        source_file_id: str,
    ) -> DataSynthesisFileInstance:
        """根据任务ID和原始文件ID，查找或创建对应的 DataSynthesisFileInstance 记录。

        - 如果已存在（同一任务 + 同一 source_file_id），直接返回；
        - 如果不存在，则创建一条新的文件任务记录，file_name 来自文件路径，
          target_file_location 先复用任务的 result_data_location。
        """
        # 尝试查询已有文件任务记录
        result = await self.db.execute(
            select(DataSynthesisFileInstance).where(
                DataSynthesisFileInstance.synthesis_instance_id == synthesis_task_id,
                DataSynthesisFileInstance.source_file_id == source_file_id,
            )
        )
        file_task = result.scalar_one_or_none()
        return file_task

    async def _mark_file_failed(self, synth_task_id: str, file_id: str, reason: str | None = None) -> None:
        """将指定任务下的单个文件任务标记为失败状态，兜底错误处理。

        - 如果找到对应的 DataSynthesisFileInstance，则更新其 status="failed"。
        - 如果未找到，则静默返回，仅记录日志。
        - reason 参数仅用于日志记录，方便排查。
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
            logger.info(
                f"Marked file task as failed for task={synth_task_id}, file_id={file_id}, reason={reason}"
            )
        except Exception as e:
            # 兜底日志，避免异常向外传播影响其它文件处理
            logger.exception(
                f"Unexpected error when marking file failed for task={synth_task_id}, file_id={file_id}, original_reason={reason}, error={e}"
            )

    async def _get_file_ids_for_task(self, synth_task_id: str):
        """根据任务ID查询关联的文件原始ID列表"""
        result = await self.db.execute(
            select(DataSynthesisFileInstance.source_file_id)
            .where(DataSynthesisFileInstance.synthesis_instance_id == synth_task_id)
        )
        file_ids = result.scalars().all()
        return file_ids

    # ========== 新增：chunk 计数与批量加载、processed_chunks 安全更新辅助方法 ==========
    async def _count_chunks_for_file(self, synth_file_instance_id: str) -> int:
        """统计指定任务与文件下的 chunk 总数。"""
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.count(DataSynthesisChunkInstance.id)).where(
                DataSynthesisChunkInstance.synthesis_file_instance_id == synth_file_instance_id
            )
        )
        return int(result.scalar() or 0)

    async def _load_chunk_batch(
        self,
        file_task_id: str,
        start_index: int,
        end_index: int,
    ) -> list[DataSynthesisChunkInstance]:
        """按索引范围加载指定文件任务下的一批 chunk 记录（含边界）。"""
        result = await self.db.execute(
            select(DataSynthesisChunkInstance)
            .where(
                DataSynthesisChunkInstance.synthesis_file_instance_id == file_task_id,
                DataSynthesisChunkInstance.chunk_index >= start_index,
                DataSynthesisChunkInstance.chunk_index <= end_index,
            )
            .order_by(DataSynthesisChunkInstance.chunk_index.asc())
        )
        return list(result.scalars().all())

    async def _increment_processed_chunks(self, file_task_id: str, delta: int) -> None:
        result = await self.db.execute(
            select(DataSynthesisFileInstance).where(
                DataSynthesisFileInstance.id == file_task_id,
            )
        )
        file_task = result.scalar_one_or_none()
        if not file_task:
            logger.error(f"Failed to increment processed_chunks: file_task {file_task_id} not found")
            return

        # 原始自增
        new_value = (file_task.processed_chunks or 0) + int(delta)

        # 如果存在 total_chunks，上限为 total_chunks，避免超过
        total = file_task.total_chunks
        if isinstance(total, int) and total >= 0:
            new_value = min(new_value, total)

        file_task.processed_chunks = new_value
        await self.db.commit()
        await self.db.refresh(file_task)
