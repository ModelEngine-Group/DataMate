import asyncio
import uuid
import json
from pathlib import Path

from langchain_community.document_loaders import (
    TextLoader,
    CSVLoader,
    JSONLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader,
    UnstructuredFileLoader,
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.data_synthesis import (
    DataSynthesisInstance,
    DataSynthesisFileInstance,
    DataSynthesisChunkInstance,
    SynthesisData,
)
from app.db.models.dataset_management import DatasetFiles
from app.db.models.model_config import get_model_by_id
from app.db.session import logger
from app.module.system.service.common_service import get_chat_client, chat


class GenerationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_task(self, task_id: str):
        """处理数据合成任务入口：根据任务ID加载任务并逐个处理源文件。"""
        synthesis_task: DataSynthesisInstance | None = await self.db.get(DataSynthesisInstance, task_id)
        if not synthesis_task:
            logger.error(f"Synthesis task {task_id} not found, abort processing")
            return

        logger.info(f"Processing synthesis task {task_id}")
        file_ids = synthesis_task.source_file_id or []

        # 获取模型客户端
        model_result = await get_model_by_id(self.db, str(synthesis_task.model_id))
        if not model_result:
            logger.error(
                f"Model config not found for id={synthesis_task.model_id}, abort task {synthesis_task.id}"
            )
            return
        chat_client = get_chat_client(model_result)

        # 控制并发度的信号量（限制全任务范围内最多 10 个并发调用）
        semaphore = asyncio.Semaphore(10)

        # 逐个文件处理
        for file_id in file_ids:
            try:
                success = await self._process_single_file(
                    synthesis_task=synthesis_task,
                    file_id=file_id,
                    chat_client=chat_client,
                    semaphore=semaphore,
                )
            except Exception as e:
                logger.exception(f"Unexpected error when processing file {file_id} for task {task_id}: {e}")
                # 确保对应文件任务状态标记为失败
                await self._mark_file_failed(str(synthesis_task.id), file_id, str(e))
                success = False

            if success:
                # 每处理完一个文件，简单增加 processed_files 计数
                synthesis_task.processed_files = (synthesis_task.processed_files or 0) + 1
                await self.db.commit()
                await self.db.refresh(synthesis_task)

        logger.info(f"Finished processing synthesis task {synthesis_task.id}")

    async def _process_single_file(
        self,
        synthesis_task: DataSynthesisInstance,
        file_id: str,
        chat_client,
        semaphore: asyncio.Semaphore,
    ) -> bool:
        """处理单个源文件：解析路径、切片、保存分块并触发 LLM 调用。"""
        file_path = await self._resolve_file_path(file_id)
        if not file_path:
            logger.warning(f"File path not found for file_id={file_id}, skip")
            await self._mark_file_failed(str(synthesis_task.id), file_id, "file_path_not_found")
            return False

        logger.info(f"Processing file_id={file_id}, path={file_path}")

        split_cfg = synthesis_task.text_split_config or {}
        synthesis_cfg = synthesis_task.synthesis_config or {}
        chunk_size = int(split_cfg.get("chunk_size", 800))
        chunk_overlap = int(split_cfg.get("chunk_overlap", 50))
        # 加载并切片
        try:
            chunks = self._load_and_split(file_path, chunk_size, chunk_overlap)
        except Exception as e:
            logger.error(f"Failed to load/split file {file_path}: {e}")
            await self._mark_file_failed(str(synthesis_task.id), file_id, f"load_split_error: {e}")
            return False

        if not chunks:
            logger.warning(f"No chunks generated for file_id={file_id}")
            await self._mark_file_failed(str(synthesis_task.id), file_id, "no_chunks_generated")
            return False

        logger.info(f"File {file_id} split into {len(chunks)} chunks by LangChain")

        # 保存文件任务记录 + 分块记录
        file_task = await self._get_or_create_file_instance(
            synthesis_task_id=str(synthesis_task.id),
            source_file_id=file_id,
            file_path=file_path,
        )
        await self._persist_chunks(synthesis_task, file_task, file_id, chunks)

        # 针对每个切片并发调用大模型
        await self._invoke_llm_for_chunks(
            synthesis_task=synthesis_task,
            file_id=file_id,
            chunks=chunks,
            synthesis_cfg=synthesis_cfg,
            chat_client=chat_client,
            semaphore=semaphore,
        )

        # 如果执行到此处，说明该文件的切片与 LLM 调用流程均未抛出异常，标记为完成
        file_task.status = "completed"
        await self.db.commit()
        await self.db.refresh(file_task)

        return True

    async def _persist_chunks(
        self,
        synthesis_task: DataSynthesisInstance,
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

    async def _invoke_llm_for_chunks(
        self,
        synthesis_task: DataSynthesisInstance,
        file_id: str,
        chunks,
        synthesis_cfg: dict,
        chat_client,
        semaphore: asyncio.Semaphore,
    ) -> None:
        """针对每个分片并发调用大模型生成数据。"""
        # 需要将 answer 和对应 chunk 建立关系，因此这里保留 chunk_index
        tasks = [
            self._call_llm(doc, file_id, idx, synthesis_task, synthesis_cfg, chat_client, semaphore)
            for idx, doc in enumerate(chunks, start=1)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _call_llm(
        self,
        doc,
        file_id: str,
        idx: int,
        synthesis_task,
        synthesis_cfg: dict,
        chat_client,
        semaphore: asyncio.Semaphore,
    ):
        """单次大模型调用逻辑，带并发控制。

        说明：
        - 使用信号量限制全局并发量（当前为 10）。
        - 使用线程池执行同步的 chat 调用，避免阻塞事件循环。
        - 在拿到 LLM 返回后，解析为 JSON 并批量写入 SynthesisData，
          同时更新文件级 processed_chunks / 进度等信息。
        """
        async with semaphore:
            prompt = self._build_qa_prompt(doc.page_content, synthesis_cfg)
            try:
                loop = asyncio.get_running_loop()
                answer = await loop.run_in_executor(None, chat, chat_client, prompt)
                logger.debug(
                    f"Generated QA for task={synthesis_task.id}, file={file_id}, chunk={idx}"
                )
                await self._handle_llm_answer(
                    synthesis_task_id=str(synthesis_task.id),
                    file_id=file_id,
                    chunk_index=idx,
                    raw_answer=answer,
                )
                return answer
            except Exception as e:
                logger.error(
                    f"LLM generation failed for task={synthesis_task.id}, file={file_id}, chunk={idx}: {e}"
                )
                return None

    async def _resolve_file_path(self, file_id: str) -> str | None:
        """根据文件ID查询 t_dm_dataset_files 并返回 file_path（仅 ACTIVE 文件）。"""
        result = await self.db.execute(
            select(DatasetFiles).where(DatasetFiles.id == file_id)
        )
        file_obj = result.scalar_one_or_none()
        if not file_obj:
            return None
        return file_obj.file_path

    def _load_and_split(self, file_path: str, chunk_size: int, chunk_overlap: int):
        """使用 LangChain 加载文本并进行切片，直接返回 Document 列表。

        当前实现：
        - 使用 TextLoader 加载纯文本/Markdown/JSON 等文本文件
        - 使用 RecursiveCharacterTextSplitter 做基于字符的递归切片

        保留每个 Document 的 metadata，方便后续追加例如文件ID、chunk序号等信息。
        """
        loader = self._build_loader(file_path)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            # 尝试按这些分隔符优先切分，再退化到字符级
            separators=["\n\n", "\n", "。", "！", "？", "!", "?", "。\n", "\t", " "]
        )
        split_docs = splitter.split_documents(docs)
        return split_docs

    @staticmethod
    def _build_loader(file_path: str):
        """根据文件扩展名选择合适的 LangChain 文本加载器，尽量覆盖常见泛文本格式。

        优先按格式选择专门的 Loader，找不到匹配时退回到 TextLoader。
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        path_str = str(path)

        # 1. 纯文本类
        if suffix in {".txt", "", ".log"}:  # "" 兼容无扩展名
            return TextLoader(path_str, encoding="utf-8")

        # 2. Markdown
        if suffix in {".md", ".markdown"}:
            # UnstructuredMarkdownLoader 会保留更多结构信息
            return UnstructuredMarkdownLoader(path_str)

        # 3. HTML / HTM
        if suffix in {".html", ".htm"}:
            return UnstructuredHTMLLoader(path_str)

        # 4. JSON
        if suffix == ".json":
            # 使用 JSONLoader 将 JSON 中的内容展开成文档
            # 这里使用默认 jq_schema，后续需要更精细地提取可以在此调整
            return JSONLoader(file_path=path_str, jq_schema=".")

        # 5. CSV / TSV
        if suffix in {".csv", ".tsv"}:
            # CSVLoader 默认将每一行作为一条 Document
            return CSVLoader(file_path=path_str)

        # 6. YAML
        if suffix in {".yaml", ".yml"}:
            # 暂时按纯文本加载
            return TextLoader(path_str, encoding="utf-8")

        # 7. PDF
        if suffix == ".pdf":
            return PyPDFLoader(path_str)

        # 8. Word 文档
        if suffix in {".docx", ".doc"}:
            # UnstructuredWordDocumentLoader 支持 .docx/.doc 文本抽取
            return UnstructuredWordDocumentLoader(path_str)

        # 9. PowerPoint
        if suffix in {".ppt", ".pptx"}:
            return UnstructuredPowerPointLoader(path_str)

        # 10. Excel
        if suffix in {".xls", ".xlsx"}:
            return UnstructuredExcelLoader(path_str)

        # 11. 兜底：使用 UnstructuredFileLoader 或 TextLoader 作为纯文本
        try:
            return UnstructuredFileLoader(path_str)
        except Exception:
            return TextLoader(path_str, encoding="utf-8")

    @staticmethod
    def _build_qa_prompt(chunk: str, synthesis_cfg: dict) -> str:
        """构造 QA 数据合成的提示词。

        要求：
        - synthesis_cfg["prompt_template"] 是一个字符串，其中包含 {document} 占位符；
        - 将当前切片内容替换到 {document}。
        如果未提供或模板非法，则使用内置默认模板。
        """
        template = None
        if isinstance(synthesis_cfg, dict):
            template = synthesis_cfg.get("prompt_template")
        synthesis_count = synthesis_cfg["synthesis_count"] if ("synthesis_count" in synthesis_cfg and synthesis_cfg["synthesis_count"]) else 5
        try:
            prompt = template.format(document=chunk, synthesis_count=synthesis_count)
        except Exception:
            # 防御性处理：如果 format 出现异常，则退回到简单拼接
            prompt = f"{template}\n\n文档内容：{chunk}\n\n请根据文档内容生成 {synthesis_count} 条符合要求的问答数据。"
        return prompt

    async def _handle_llm_answer(
        self,
        synthesis_task_id: str,
        file_id: str,
        chunk_index: int,
        raw_answer: str,
    ) -> None:
        """解析 LLM 返回内容为 JSON，批量保存到 SynthesisData，并更新文件任务进度。

        约定：
        - LLM 返回的 raw_answer 是 JSON 字符串，可以是：
          1）单个对象：{"question": ..., "answer": ...}
          2）对象数组：[{}, {}, ...]
        - 我们将其规范化为列表，每个元素作为一条 SynthesisData.data 写入。
        - 根据 synthesis_task_id + file_id + chunk_index 找到对应的 DataSynthesisChunkInstance，
          以便设置 chunk_instance_id 和 synthesis_file_instance_id。
        - 每处理完一个 chunk，递增对应 DataSynthesisFileInstance.processed_chunks，并按比例更新进度。
        """
        if not raw_answer:
            return

        # 1. 预处理原始回答：尝试从中截取出最可能的 JSON 片段
        cleaned = self._extract_json_substring(raw_answer)

        # 2. 解析 JSON，统一成列表结构
        try:
            parsed = json.loads(cleaned)
        except Exception as e:
            logger.error(
                f"Failed to parse LLM answer as JSON for task={synthesis_task_id}, file={file_id}, chunk={chunk_index}: {e}. Raw answer: {raw_answer!r}"
            )
            return

        if isinstance(parsed, dict):
            items = [parsed]
        elif isinstance(parsed, list):
            items = [p for p in parsed if isinstance(p, dict)]
        else:
            logger.error(f"Unexpected JSON structure from LLM answer for task={synthesis_task_id}, file={file_id}, chunk={chunk_index}: {type(parsed)}")
            return

        if not items:
            return

        # 3. 找到对应的 chunk 记录（一个 chunk_index 对应一条记录）
        chunk_result = await self.db.execute(
            select(DataSynthesisChunkInstance, DataSynthesisFileInstance)
            .join(
                DataSynthesisFileInstance,
                DataSynthesisFileInstance.id == DataSynthesisChunkInstance.synthesis_file_instance_id,
            )
            .where(
                DataSynthesisFileInstance.synthesis_instance_id == synthesis_task_id,
                DataSynthesisFileInstance.source_file_id == file_id,
                DataSynthesisChunkInstance.chunk_index == chunk_index,
            )
        )
        row = chunk_result.first()
        if not row:
            logger.error(
                f"Chunk record not found for task={synthesis_task_id}, file={file_id}, chunk_index={chunk_index}, skip saving SynthesisData."
            )
            return

        chunk_instance, file_instance = row

        # 4. 批量写入 SynthesisData
        for data_obj in items:
            record = SynthesisData(
                id=str(uuid.uuid4()),
                data=data_obj,
                synthesis_file_instance_id=file_instance.id,
                chunk_instance_id=chunk_instance.id,
            )
            self.db.add(record)

        # 5. 更新文件级 processed_chunks / 进度
        file_instance.processed_chunks = (file_instance.processed_chunks or 0) + 1


        await self.db.commit()
        await self.db.refresh(file_instance)

    @staticmethod
    def _extract_json_substring(raw: str) -> str:
        """从 LLM 的原始回答中提取最可能的 JSON 字符串片段。

        处理思路：
        - 原始回答可能是：说明文字 + JSON + 说明文字，甚至带有 Markdown 代码块。
        - 优先在文本中查找第一个 '{' 或 '[' 作为 JSON 起始；
        - 再从后向前找最后一个 '}' 或 ']' 作为结束；
        - 如果找不到合适的边界，就退回原始字符串。
        该方法不会保证截取的一定是合法 JSON，但能显著提高 json.loads 的成功率。
        """
        if not raw:
            return raw

        start = None
        end = None

        # 查找第一个 JSON 起始符号
        for i, ch in enumerate(raw):
            if ch in "[{":
                start = i
                break

        # 查找最后一个 JSON 结束符号
        for i in range(len(raw) - 1, -1, -1):
            if raw[i] in "]}":
                end = i + 1  # 切片是左闭右开
                break

        if start is not None and end is not None and start < end:
            return raw[start:end].strip()

        # 兜底：去掉常见 Markdown 包裹（```json ... ```）
        stripped = raw.strip()
        if stripped.startswith("```"):
            # 去掉首尾 ``` 标记
            stripped = stripped.strip("`")
        return stripped

    async def _get_or_create_file_instance(
        self,
        synthesis_task_id: str,
        source_file_id: str,
        file_path: str,
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
        if file_task is not None:
            return file_task

        # 查询任务以获取 result_data_location
        task = await self.db.get(DataSynthesisInstance, synthesis_task_id)
        target_location = task.result_data_location if task else ""

        # 创建新的文件任务记录，初始状态为 processing
        file_task = DataSynthesisFileInstance(
            id=str(uuid.uuid4()),
            synthesis_instance_id=synthesis_task_id,
            file_name=Path(file_path).name,
            source_file_id=source_file_id,
            target_file_location=target_location or "",
            status="processing",
            total_chunks=0,
            processed_chunks=0,
            created_by="system",
            updated_by="system",
        )
        self.db.add(file_task)
        await self.db.commit()
        await self.db.refresh(file_task)
        return file_task

    async def _mark_file_failed(self, synthesis_task_id: str, file_id: str, reason: str | None = None) -> None:
        """将指定任务下的单个文件任务标记为失败状态，兜底错误处理。

        - 如果找到对应的 DataSynthesisFileInstance，则更新其 status="failed"。
        - 如果未找到，则静默返回，仅记录日志。
        - reason 参数仅用于日志记录，方便排查。
        """
        try:
            result = await self.db.execute(
                select(DataSynthesisFileInstance).where(
                    DataSynthesisFileInstance.synthesis_instance_id == synthesis_task_id,
                    DataSynthesisFileInstance.source_file_id == file_id,
                )
            )
            file_task = result.scalar_one_or_none()
            if not file_task:
                logger.warning(
                    f"Failed to mark file as failed: no DataSynthesisFileInstance found for task={synthesis_task_id}, file_id={file_id}, reason={reason}"
                )
                return

            file_task.status = "failed"
            await self.db.commit()
            await self.db.refresh(file_task)
            logger.info(
                f"Marked file task as failed for task={synthesis_task_id}, file_id={file_id}, reason={reason}"
            )
        except Exception as e:
            # 兜底日志，避免异常向外传播影响其它文件处理
            logger.exception(
                f"Unexpected error when marking file failed for task={synthesis_task_id}, file_id={file_id}, original_reason={reason}, error={e}"
            )
