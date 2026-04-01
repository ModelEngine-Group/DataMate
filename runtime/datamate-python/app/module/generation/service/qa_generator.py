"""问答生成器模块 - 负责问题生成和答案生成"""
import asyncio
import json
import re
import uuid
from typing import Any

from langchain_core.language_models import BaseChatModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.data_synthesis import (
    DataSynthesisChunkInstance,
    DataSynthesisFileInstance,
    SynthesisData,
)
from app.db.session import logger
from app.module.generation.schema.generation import SyntheConfig
from app.module.generation.service.prompt import (
    ANSWER_GENERATOR_PROMPT,
    QUESTION_GENERATOR_PROMPT,
)
from app.module.shared.util.model_chat import extract_json_substring
from app.module.shared.llm import LLMFactory


# 图片URL提取正则
IMG_URL_PATTERN = re.compile(r"!\[\]\((.*?)\)")


def extract_img_urls(text: str) -> list[str]:
    """提取文本中的图片URL"""
    return IMG_URL_PATTERN.findall(text)


def _filter_docs_by_size(docs: list[Any], chunk_size: int, ratio: float = 0.7) -> list[Any]:
    """过滤文档，保留长度大于 chunk_size * ratio 的文档

    Args:
        docs: 文档列表
        chunk_size: 切片大小
        ratio: 长度比例阈值

    Returns:
        过滤后的文档列表
    """
    min_length = chunk_size * ratio
    return [doc for doc in docs if len(doc.page_content) >= min_length]


class QuestionGenerator:
    """问题生成器"""

    def __init__(self, db: AsyncSession, semaphore: asyncio.Semaphore | None = None):
        self.db = db
        self.semaphore = semaphore or asyncio.Semaphore(10)

    async def generate_questions(
        self,
        chunk_text: str,
        question_cfg: SyntheConfig,
        question_chat: BaseChatModel,
    ) -> list[str]:
        """针对单个切片文本，调用模型生成问题列表

        Args:
            chunk_text: 切片文本内容
            question_cfg: 问题生成配置
            question_chat: 问题生成模型

        Returns:
            问题列表
        """
        # 计算问题数量：每千tokens生成指定数量的问题
        base_number = question_cfg.number or 5
        calculated_number = max(int(len(chunk_text) / 1000 * base_number), 1)

        # 获取提示模板
        template = getattr(question_cfg, "prompt_template", None)
        template = template if template and template.strip() else QUESTION_GENERATOR_PROMPT

        # 构建提示
        prompt = (
            template
            .replace("{text}", chunk_text)
            .replace("{number}", str(calculated_number))
            .replace("{textLength}", str(len(chunk_text)))
        )

        # 调用模型
        async with self.semaphore:
            loop = asyncio.get_running_loop()
            raw_answer = await loop.run_in_executor(
                None,
                LLMFactory.invoke_sync,
                question_chat,
                prompt,
            )

        # 解析问题列表
        return self._parse_questions(raw_answer)

    def _parse_questions(self, raw_answer: str) -> list[str]:
        """从模型返回中解析问题列表

        Args:
            raw_answer: 模型原始返回

        Returns:
            问题列表
        """
        if not raw_answer:
            return []

        cleaned = extract_json_substring(raw_answer)
        try:
            data = json.loads(cleaned)
        except Exception as e:
            logger.error(f"Failed to parse question list JSON: {e}")
            return []

        if isinstance(data, list):
            return [str(q) for q in data if isinstance(q, str) and q.strip()]

        # 容错：如果是单个字符串
        if isinstance(data, str) and data.strip():
            return [data.strip()]

        return []


class AnswerGenerator:
    """答案生成器"""

    def __init__(self, db: AsyncSession, semaphore: asyncio.Semaphore | None = None):
        self.db = db
        self.semaphore = semaphore or asyncio.Semaphore(10)

    async def generate_answers_for_chunk(
        self,
        file_task: DataSynthesisFileInstance,
        chunk: DataSynthesisChunkInstance,
        questions: list[str],
        answer_cfg: SyntheConfig,
        answer_chat: BaseChatModel,
    ) -> int:
        """为一个切片的所有问题生成答案并写入数据库

        Args:
            file_task: 文件任务实例
            chunk: 切片实例
            questions: 问题列表
            answer_cfg: 答案生成配置
            answer_chat: 答案生成模型

        Returns:
            成功生成的QA对数量
        """
        if not questions:
            return 0

        chunk_text = chunk.chunk_content or ""
        template = getattr(answer_cfg, "prompt_template", None)
        template = template if template and template.strip() else ANSWER_GENERATOR_PROMPT

        success_count = 0

        async def process_question(question: str) -> bool:
            nonlocal success_count
            try:
                prompt = template.replace("{text}", chunk_text).replace("{question}", question)

                async with self.semaphore:
                    loop = asyncio.get_running_loop()
                    answer = await loop.run_in_executor(
                        None,
                        LLMFactory.invoke_sync,
                        answer_chat,
                        prompt,
                    )

                # 构建数据对象
                data_obj = self._build_synthesis_data(chunk_text, question, answer)

                # 保存记录
                record = SynthesisData(
                    id=str(uuid.uuid4()),
                    data=data_obj,
                    synthesis_file_instance_id=file_task.id,
                    chunk_instance_id=chunk.id,
                )
                self.db.add(record)
                success_count += 1
                return True

            except Exception as e:
                logger.error(f"Failed to generate answer for question '{question[:50]}...': {e}")
                return False

        # 并行处理所有问题
        tasks = [process_question(q) for q in questions]
        await asyncio.gather(*tasks, return_exceptions=True)

        if success_count > 0:
            await self.db.commit()

        return success_count

    def _build_synthesis_data(
        self,
        chunk_text: str,
        question: str,
        answer: str,
    ) -> dict[str, Any]:
        """构建合成数据结构

        Args:
            chunk_text: 切片原文
            question: 问题
            answer: 答案

        Returns:
            结构化数据字典
        """
        # 基础结构
        base_obj: dict[str, Any] = {
            "input": chunk_text,
            "output": answer,
        }

        # 尝试解析模型返回的JSON
        parsed_obj: dict[str, Any] | None = None
        if isinstance(answer, str):
            cleaned = extract_json_substring(answer)
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict):
                    parsed_obj = parsed
            except Exception:
                parsed_obj = None

        # 合并解析结果
        if parsed_obj is not None:
            parsed_obj["instruction"] = question
            data_obj = parsed_obj
        else:
            base_obj["instruction"] = question
            data_obj = base_obj

        # 提取图片URL
        img_urls = extract_img_urls(chunk_text)
        if img_urls:
            data_obj["img_urls"] = img_urls

        return data_obj


class QAGenerator:
    """问答生成器 - 整合问题和答案生成"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.question_semaphore = asyncio.Semaphore(10)
        self.answer_semaphore = asyncio.Semaphore(10)
        self.question_generator = QuestionGenerator(db, self.question_semaphore)
        self.answer_generator = AnswerGenerator(db, self.answer_semaphore)

    async def process_chunk_qa(
        self,
        file_task: DataSynthesisFileInstance,
        chunk: DataSynthesisChunkInstance,
        question_cfg: SyntheConfig,
        answer_cfg: SyntheConfig,
        question_chat: Any,
        answer_chat: Any,
    ) -> int:
        """处理单个切片的QA生成

        Args:
            file_task: 文件任务实例
            chunk: 切片实例
            question_cfg: 问题生成配置
            answer_cfg: 答案生成配置
            question_chat: 问题生成模型
            answer_chat: 答案生成模型

        Returns:
            成功生成的QA对数量
        """
        chunk_text = chunk.chunk_content or ""
        if not chunk_text.strip():
            logger.warning(f"Empty chunk text for chunk_index={chunk.chunk_index}")
            return 0

        # 1. 生成问题
        try:
            questions = await self.question_generator.generate_questions(
                chunk_text=chunk_text,
                question_cfg=question_cfg,
                question_chat=question_chat,
            )
        except Exception as e:
            logger.error(f"Generate questions failed: {e}")
            questions = []

        if not questions:
            logger.info(f"No questions generated for chunk_index={chunk.chunk_index}")
            return 0

        # 2. 生成答案
        success_count = await self.answer_generator.generate_answers_for_chunk(
            file_task=file_task,
            chunk=chunk,
            questions=questions,
            answer_cfg=answer_cfg,
            answer_chat=answer_chat,
        )

        return success_count

    async def check_qa_limit(
        self,
        synth_task_id: str,
        max_qa_pairs: int | None,
    ) -> bool:
        """检查是否已达到QA对数量上限

        Args:
            synth_task_id: 合成任务ID
            max_qa_pairs: 最大QA对数量限制

        Returns:
            是否已达到上限
        """
        if max_qa_pairs is None or max_qa_pairs <= 0:
            return False

        result = await self.db.execute(
            select(func.count(SynthesisData.id)).where(
                SynthesisData.synthesis_file_instance_id.in_(
                    select(DataSynthesisFileInstance.id).where(
                        DataSynthesisFileInstance.synthesis_instance_id == synth_task_id
                    )
                )
            )
        )
        current_count = int(result.scalar() or 0)

        return current_count >= max_qa_pairs
