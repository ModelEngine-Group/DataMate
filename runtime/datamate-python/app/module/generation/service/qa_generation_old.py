from typing import List, Optional, Dict, Any
import json
import asyncio
from datetime import datetime

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from openai import OpenAI
from loguru import logger

from app.core.logging import get_logger
from app.db.models.qa_generation import QAGenerationInstance
from app.db.models import Dataset
from app.module.generation.service.text_splitter import TextSplitter

logger = get_logger(__name__)


class QAGenerationService:
    """QA生成任务服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(
        self,
        *,
        name: str,
        description: Optional[str],
        source_dataset_id: str,
        text_split_config: Dict[str, Any],
        qa_generation_config: Dict[str, Any],
        llm_api_key: str,
        llm_base_url: str,
        target_dataset_id: Optional[str] = None,
    ) -> QAGenerationInstance:
        """创建QA生成任务实例
        
        Args:
            name: 任务名称
            description: 任务描述
            source_dataset_id: 源数据集ID
            text_split_config: 文本切片配置
            qa_generation_config: QA生成配置
            llm_api_key: LLM API密钥
            llm_base_url: LLM Base URL
            target_dataset_id: 目标数据集ID (可选)
            
        Returns:
            QAGenerationInstance: 创建的任务实例
        """
        logger.info(f"Creating QA generation task: name={name}, source_dataset={source_dataset_id}")

        instance = QAGenerationInstance(
            name=name,
            description=description,
            source_dataset_id=source_dataset_id,
            target_dataset_id=target_dataset_id,
            text_split_config=text_split_config,
            qa_generation_config=qa_generation_config,
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            status="PENDING",
            total_chunks=0,
            processed_chunks=0,
            total_qa_pairs=0,
        )

        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)

        logger.info(f"QA generation task created with id: {instance.id}")
        return instance

    async def get_task_by_id(self, task_id: str) -> Optional[QAGenerationInstance]:
        """根据ID获取任务"""
        result = await self.db.execute(
            select(QAGenerationInstance).where(QAGenerationInstance.id == task_id)
        )
        return result.scalar_one_or_none()

    async def list_tasks(
        self,
        *,
        page: int = 0,
        size: int = 10,
        name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> tuple[List[QAGenerationInstance], int]:
        """分页查询任务列表
        
        Returns:
            tuple: (任务列表, 总数)
        """
        # 构建查询条件
        conditions = []
        if name:
            conditions.append(QAGenerationInstance.name.like(f"%{name}%"))
        if status:
            conditions.append(QAGenerationInstance.status == status)

        # 查询总数
        count_query = select(func.count()).select_from(QAGenerationInstance)
        if conditions:
            for cond in conditions:
                count_query = count_query.where(cond)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # 分页查询
        query = select(QAGenerationInstance)
        if conditions:
            for cond in conditions:
                query = query.where(cond)
        query = query.order_by(QAGenerationInstance.created_at.desc())
        query = query.offset(page * size).limit(size)

        result = await self.db.execute(query)
        tasks = result.scalars().all()

        return list(tasks), total

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> Optional[QAGenerationInstance]:
        """更新任务状态"""
        task = await self.get_task_by_id(task_id)
        if not task:
            return None

        task.status = status
        if error_message:
            task.error_message = error_message

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def update_task_progress(
        self,
        task_id: str,
        total_chunks: Optional[int] = None,
        processed_chunks: Optional[int] = None,
        total_qa_pairs: Optional[int] = None,
    ) -> Optional[QAGenerationInstance]:
        """更新任务进度"""
        task = await self.get_task_by_id(task_id)
        if not task:
            return None

        if total_chunks is not None:
            task.total_chunks = total_chunks
        if processed_chunks is not None:
            task.processed_chunks = processed_chunks
        if total_qa_pairs is not None:
            task.total_qa_pairs = total_qa_pairs

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        result = await self.db.execute(
            delete(QAGenerationInstance).where(QAGenerationInstance.id == task_id)
        )
        await self.db.commit()
        return result.rowcount > 0

    def create_text_splitter(self, config: Dict[str, Any]) -> TextSplitter:
        """根据配置创建文本切片器"""
        return TextSplitter(
            max_characters=config.get("max_characters", 50000),
            chunk_size=config.get("chunk_size", 800),
            chunk_overlap=config.get("chunk_overlap", 200),
        )

    def extract_json(self, text: str) -> str:
        """
        从 LLM 输出中严格提取第一段合法 JSON。
        自动处理：
        - 多余说明
        - 代码块 ```json ... ```
        - 前后空行
        - 多段 JSON（取第一段）
        """
        import re

        # 去掉代码块 ``` ```
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"```[a-zA-Z]*", "", text)
            text = text.replace("```", "").strip()

        # 用正则找最长的 {...} 块
        json_matches = re.findall(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", text, re.DOTALL)

        if not json_matches:
            raise ValueError("No JSON object found in model output")

        # 返回第一个 JSON（一般只有一个）
        return json_matches[0]

    def generate_qa_for_chunk(
        self,
        chunk: str,
        llm_client: OpenAI,
        model: str,
        max_questions: int,
        temperature: float,
    ) -> Dict[str, str]:
        """为单个文本块生成QA对
        
        Args:
            chunk: 文本块
            llm_client: OpenAI客户端
            model: 模型名称
            max_questions: 最大问题数
            temperature: 温度参数
            
        Returns:
            Dict: {"问题1": "答案1", "问题2": "答案2", ...}
        """
        QA_PROMPT = """你是一个高级阅读理解与知识抽取专家。请根据下面的文本片段生成若干组"问题-答案(Q&A)"对。

【问题数量要求】
- 用户允许的最大问题数量为：{max_q}。
- 实际生成的问题数量必须在 1 到 {max_q} 之间，由你根据文本内容的信息密度自动决定。
- 若文本信息量较少,请只生成 1 个综合性问题；
- 若文本信息量较大，可以生成多个相对简短的问题来覆盖不同要点。

【问题设计规则】
1. 若只生成 1 个问题：该问题应覆盖文本片段的大部分核心信息，可适当加长。
2. 若生成多个问题：每个问题都应聚焦于该片段的某一部分信息，避免重复，覆盖全部重要内容。
3. 问题和答案必须完全基于文本，不得引入文本外内容。
4. 答案必须简洁准确，不要逐句复述整段内容。
5. 输出必须是严格合法 JSON，不包含任何解释性文字。

【JSON 输出格式（示例）】
{{
  "问题1": "……",
  "答案1": "……",
  "问题2": "……",
  "答案2": "……",
  ...
}}

以下是文本片段：
{text}
"""
        prompt = QA_PROMPT.format(text=chunk, max_q=max_questions)

        try:
            resp = llm_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            content = resp.choices[0].message.content.strip()

            try:
                json_text = self.extract_json(content)    # ← 强力 JSON 修复
                qa = json.loads(json_text)                # ← 确保一定成功
            except Exception as e:
                logger.error(f"Model output invalid JSON: {content}")
                raise e
            # content = resp.choices[0].message.content.strip()
            # qa = json.loads(content)
            return qa

        except Exception as e:
            logger.error(f"Failed to generate QA for chunk: {e}")
            raise

    async def process_task(self, task_id: str) -> None:
        """执行QA生成任务 (后台任务)
        
        这个方法应该在后台异步执行，处理流程:
        1. 从源数据集或本地文件读取文本
        2. 文本切片
        3. 为每个切片生成QA对
        4. 将结果保存到目标数据集
        5. 更新任务状态和进度
        """
        try:
            # 更新任务状态为运行中
            await self.update_task_status(task_id, "RUNNING")

            # 获取任务
            task = await self.get_task_by_id(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")

            # 初始化 LLM 客户端
            llm_client = OpenAI(
                api_key=task.llm_api_key,
                base_url=task.llm_base_url,
            )

            # 从源读取文本数据
            source_info = task.text_split_config.get("source_info", {})
            if source_info.get("type") == "file":
                # 从本地文件读取
                file_path = source_info.get("path")
                logger.info(f"Reading from local file: {file_path}")
                with open(file_path, "r", encoding="utf-8") as f:
                    source_text = f.read()
                logger.info(f"Read {len(source_text)} characters from file")
            else:
                # 从数据集读取
                # TODO: 实现从数据集读取的逻辑
                logger.warning("Reading from dataset is not implemented yet")
                source_text = ""  # 需要实现实际的数据读取逻辑

            # 创建文本切片器
            splitter = self.create_text_splitter(task.text_split_config)
            chunks = splitter.split_text(source_text)

            # 更新总块数
            await self.update_task_progress(task_id, total_chunks=len(chunks))

            # 生成QA对
            all_qa_pairs = []
            qa_config = task.qa_generation_config
            
            for idx, chunk in enumerate(chunks, start=1):
                try:
                    qa = self.generate_qa_for_chunk(
                        chunk=chunk,
                        llm_client=llm_client,
                        model=qa_config.get("model", "gpt-5-nano"),
                        max_questions=qa_config.get("max_questions", 3),
                        temperature=qa_config.get("temperature", 0.3),
                    )
                    
                    all_qa_pairs.append({
                        f"文本块{idx}": {
                            "文本": chunk,
                            **qa
                        }
                    })

                    # 更新进度
                    await self.update_task_progress(
                        task_id,
                        processed_chunks=idx,
                        total_qa_pairs=len(all_qa_pairs),
                    )

                except Exception as e:
                    logger.error(f"Failed to process chunk {idx}: {e}")
                    continue

            # TODO: 将QA对保存到目标数据集
            # await self.save_qa_to_dataset(task.target_dataset_id, all_qa_pairs)

            # 更新任务状态为完成
            await self.update_task_status(task_id, "COMPLETED")

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            await self.update_task_status(task_id, "FAILED", str(e))
            raise
