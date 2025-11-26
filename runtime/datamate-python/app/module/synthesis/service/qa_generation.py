from typing import List, Optional, Dict, Any
import json
import os
from pathlib import Path
from datetime import datetime

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from openai import OpenAI
from loguru import logger

from app.core.logging import get_logger
from app.db.models.qa_generation import QAGenerationInstance, QAPair
from app.db.models.dataset_management import Dataset, DatasetFiles
from app.module.synthesis.service.text_splitter import TextSplitter

logger = get_logger(__name__)


class QAGenerationService:
    """QA生成任务服务
    
    完整数据流:
    1. 从 t_dm_dataset_files 读取源数据集中的所有 .txt 文件
    2. 对每个文件进行文本切片和QA生成
    3. 将QA对存入 t_qa_pairs 表 (text_chunk, question, answer三列)
    4. 读取 t_qa_pairs 数据转换成 JSONL 格式
    5. 以原始文件名生成对应的 .jsonl 文件 (如 abc.txt -> abc.jsonl)
    6. 将生成的 JSONL 文件存入 t_dm_dataset_files (新的目标数据集)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(
        self,
        *,
        name: str,
        description: Optional[str],
        source_file_ids: List[str],
        text_split_config: Dict[str, Any],
        qa_generation_config: Dict[str, Any],
        llm_api_key: str,
        llm_base_url: str,
        extra_prompt: Optional[str] = None,
        target_dataset_id: Optional[str] = None,
    ) -> QAGenerationInstance:
        """创建QA生成任务实例
        
        Args:
            source_file_ids: 源文件ID列表（来自 t_dm_dataset_files）
            extra_prompt: 用户自定义提示词，会插入到 LLM Prompt 中
        """
        logger.info(f"Creating QA generation task: name={name}, file_count={len(source_file_ids)}")

        instance = QAGenerationInstance(
            name=name,
            description=description,
            source_dataset_id=json.dumps(source_file_ids),  # 将 file_ids 存储为 JSON
            target_dataset_id=target_dataset_id,
            text_split_config=text_split_config,
            qa_generation_config=qa_generation_config,
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            status="PENDING",
            total_files=len(source_file_ids),
            processed_files=0,
            total_chunks=0,
            processed_chunks=0,
            total_qa_pairs=0,
        )
        
        # 如果有 extra_prompt，存入 qa_generation_config
        if extra_prompt:
            instance.qa_generation_config["extra_prompt"] = extra_prompt

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
        """分页查询任务列表"""
        conditions = []
        if name:
            conditions.append(QAGenerationInstance.name.like(f"%{name}%"))
        if status:
            conditions.append(QAGenerationInstance.status == status)

        count_query = select(func.count()).select_from(QAGenerationInstance)
        if conditions:
            for cond in conditions:
                count_query = count_query.where(cond)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

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
        total_files: Optional[int] = None,
        processed_files: Optional[int] = None,
        total_chunks: Optional[int] = None,
        processed_chunks: Optional[int] = None,
        total_qa_pairs: Optional[int] = None,
    ) -> Optional[QAGenerationInstance]:
        """更新任务进度"""
        task = await self.get_task_by_id(task_id)
        if not task:
            return None

        if total_files is not None:
            task.total_files = total_files
        if processed_files is not None:
            task.processed_files = processed_files
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
        # 先删除相关的QA对
        await self.db.execute(delete(QAPair).where(QAPair.task_id == task_id))
        
        # 再删除任务
        result = await self.db.execute(
            delete(QAGenerationInstance).where(QAGenerationInstance.id == task_id)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def get_source_files_by_ids(self, file_ids: List[str]) -> List[DatasetFiles]:
        """根据 file_ids 列表从 t_dm_dataset_files 获取文件
        
        支持的文件格式: .txt, .md, .json
        """
        result = await self.db.execute(
            select(DatasetFiles)
            .where(DatasetFiles.id.in_(file_ids))
            .where(DatasetFiles.status == 'ACTIVE')
        )
        files = result.scalars().all()
        
        # 过滤掉不支持的文件类型
        supported_files = []
        for f in files:
            file_ext = Path(f.file_name).suffix.lower()
            if file_ext in ['.txt', '.md', '.json']:
                supported_files.append(f)
            else:
                logger.warning(f"不支持的文件类型: {f.file_name} ({file_ext})")
        
        logger.info(f"Found {len(supported_files)}/{len(files)} supported files from {len(file_ids)} requested IDs")
        return supported_files

    async def get_source_files(self, dataset_id: str) -> List[DatasetFiles]:
        """从 t_dm_dataset_files 获取源数据集中的所有 .txt 文件（旧版本，保留兼容）"""
        result = await self.db.execute(
            select(DatasetFiles)
            .where(DatasetFiles.dataset_id == dataset_id)
            .where(DatasetFiles.file_type.in_(['txt', 'TXT', '.txt']))
            .where(DatasetFiles.status == 'ACTIVE')
        )
        files = result.scalars().all()
        logger.info(f"Found {len(files)} txt files in dataset {dataset_id}")
        return list(files)

    def create_text_splitter(self, config: Dict[str, Any]) -> TextSplitter:
        """根据配置创建文本切片器"""
        return TextSplitter(
            max_characters=config.get("max_characters", 50000),
            chunk_size=config.get("chunk_size", 800),
            chunk_overlap=config.get("chunk_overlap", 200),
        )
    
    def extract_text_from_file(self, file_path: str) -> str:
        """从文件中提取文本内容
        
        支持的格式:
        - .txt: 直接读取
        - .md: 直接读取（Markdown 文本）
        - .json: 提取所有字符串值并拼接
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 提取的文本内容
        """
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext in ['.txt', '.md']:
                # 直接读取文本
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info(f"[文件读取] {file_ext} 格式, 长度: {len(content)}")
                return content
                
            elif file_ext == '.json':
                # 从 JSON 中提取所有文本
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                def extract_strings(obj, texts=None):
                    """递归提取所有字符串"""
                    if texts is None:
                        texts = []
                    
                    if isinstance(obj, str):
                        texts.append(obj)
                    elif isinstance(obj, dict):
                        for value in obj.values():
                            extract_strings(value, texts)
                    elif isinstance(obj, list):
                        for item in obj:
                            extract_strings(item, texts)
                    
                    return texts
                
                all_texts = extract_strings(data)
                content = '\n\n'.join(all_texts)
                logger.info(f"[文件读取] JSON 格式, 提取 {len(all_texts)} 个字段, 总长度: {len(content)}")
                return content
            
            else:
                raise ValueError(f"不支持的文件格式: {file_ext}")
                
        except Exception as e:
            logger.error(f"[文件读取失败] {file_path}: {e}")
            raise

    def generate_qa_for_chunk(
        self,
        chunk: str,
        llm_client: OpenAI,
        model: str,
        max_questions: int,
        temperature: float,
        extra_prompt: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """为单个文本块生成QA对
        
        Args:
            extra_prompt: 用户自定义提示词，会插入到 Prompt 中
        
        Returns:
            List[Dict]: [{"question": "...", "answer": "..."}, ...]
        """
        # 构建提示词，如果有 extra_prompt 则插入
        extra_instruction = extra_prompt if extra_prompt else "无额外要求"
        
        QA_PROMPT = """你是一个高级阅读理解与知识抽取专家。请根据下面的文本片段生成若干组"问题-答案(Q&A)"对。

【问题数量要求】
- 用户允许的最大问题数量为：{max_q}。
- 实际生成的问题数量必须在 1 到 {max_q} 之间，由你根据文本内容的信息密度自动决定。
- 若文本信息量较少，请只生成 1 个综合性问题；
- 若文本信息量较大，可以生成多个相对简短的问题来覆盖不同要点。

【问题设计规则】
1. 若只生成 1 个问题：该问题应覆盖文本片段的大部分核心信息，可适当加长。
2. 若生成多个问题：每个问题都应聚焦于该片段的某一部分信息，避免重复，覆盖全部重要内容。
3. 问题和答案必须完全基于文本，不得引入文本外内容。
4. 答案必须简洁准确，不要逐句复述整段内容。
5. 输出必须是严格合法 JSON 数组格式，不包含任何解释性文字。
6. 【用户自定义要求】{extra_prompt}

【JSON 输出格式（示例）】
[
  {{"question": "问题1", "answer": "答案1"}},
  {{"question": "问题2", "answer": "答案2"}}
]

以下是文本片段：
{text}
"""
        prompt = QA_PROMPT.format(text=chunk, max_q=max_questions, extra_prompt=extra_instruction)

        try:
            resp = llm_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )

            content = resp.choices[0].message.content.strip()
            
            # 尝试提取JSON数组
            if content.startswith("[") and content.endswith("]"):
                qa_pairs = json.loads(content)
            else:
                # 如果不是数组格式，尝试提取第一个JSON对象
                import re
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    qa_pairs = json.loads(json_match.group())
                else:
                    logger.warning(f"Failed to parse QA response: {content[:200]}")
                    qa_pairs = []
            
            return qa_pairs

        except Exception as e:
            logger.error(f"Failed to generate QA for chunk: {e}")
            return []

    async def save_qa_pair(
        self,
        task_id: str,
        source_file_id: str,
        source_file_name: str,
        chunk_index: int,
        text_chunk: str,
        question: str,
        answer: str,
    ) -> QAPair:
        """保存单个QA对到 t_qa_pairs 表"""
        qa_pair = QAPair(
            task_id=task_id,
            source_file_id=source_file_id,
            source_file_name=source_file_name,
            chunk_index=chunk_index,
            text_chunk=text_chunk,
            question=question,
            answer=answer,
        )
        
        logger.debug(
            f"[保存QA] file={source_file_name}, chunk={chunk_index}, "
            f"Q={question[:30]}, A={answer[:30]}"
        )
        
        self.db.add(qa_pair)
        await self.db.flush()  # 使用flush而不是commit，让外层控制事务
        return qa_pair

    async def export_qa_pairs_to_jsonl(
        self,
        task_id: str,
        source_file_id: str,
        output_path: str,
    ) -> int:
        """从 t_qa_pairs 读取数据并导出为 Alpaca 格式的 JSONL 文件
        
        Alpaca 格式:
        {
            "instruction": "question",
            "input": "text_chunk",
            "output": "answer"
        }
        
        Args:
            task_id: 任务ID
            source_file_id: 源文件ID
            output_path: 输出文件路径
            
        Returns:
            int: 导出的QA对数量
        """
        logger.info(f"[导出JSONL] ========== 开始导出 ==========")
        logger.info(f"[导出JSONL] task_id={task_id}")
        logger.info(f"[导出JSONL] source_file_id={source_file_id}")
        logger.info(f"[导出JSONL] output_path={output_path}")
        
        # 查询该文件的所有QA对
        result = await self.db.execute(
            select(QAPair)
            .where(QAPair.task_id == task_id)
            .where(QAPair.source_file_id == source_file_id)
            .order_by(QAPair.chunk_index)
        )
        qa_pairs = result.scalars().all()
        
        logger.info(f"[导出JSONL] 查询到 {len(qa_pairs)} 条QA对数据")
        
        if len(qa_pairs) == 0:
            logger.error(f"[导出JSONL] ❌ 错误：没有找到QA对数据！task_id={task_id}, file_id={source_file_id}")
            logger.error(f"[导出JSONL] 请检查数据库 t_qa_pairs 表是否有数据")
            return 0
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"[导出JSONL] ✓ 输出目录已创建: {os.path.abspath(output_dir)}")
        
        # 写入JSONL文件（Alpaca 格式）
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for idx, qa in enumerate(qa_pairs, start=1):
                    # Alpaca 格式
                    record = {
                        "instruction": qa.question,
                        "input": qa.text_chunk,
                        "output": qa.answer,
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
            
            # 验证文件是否创建成功
            if not os.path.exists(output_path):
                raise FileNotFoundError(f"JSONL文件创建失败: {output_path}")
            
            file_size = os.path.getsize(output_path)
            abs_path = os.path.abspath(output_path)
            
            logger.info(f"[导出JSONL] ========== 导出成功 ==========")
            logger.info(f"[导出JSONL] ✅ 文件保存路径: {abs_path}")
            logger.info(f"[导出JSONL] ✅ 数据条数: {len(qa_pairs)} 条")
            logger.info(f"[导出JSONL] ✅ 文件大小: {file_size} bytes")
            logger.info(f"[导出JSONL] ✅ 格式: Alpaca (instruction/input/output)")
            logger.info(f"[导出JSONL] ========================================")
            
            return len(qa_pairs)
            
        except Exception as e:
            logger.error(f"[导出JSONL] ❌ 写入文件失败: {e}", exc_info=True)
            raise

    async def save_jsonl_to_dataset(
        self,
        dataset_id: str,
        file_name: str,
        file_path: str,
    ) -> DatasetFiles:
        """将生成的 JSONL 文件保存到 t_dm_dataset_files"""
        file_size = os.path.getsize(file_path)
        
        dataset_file = DatasetFiles(
            dataset_id=dataset_id,
            file_name=file_name,
            file_path=file_path,
            file_type='jsonl',
            file_size=file_size,
            status='ACTIVE',
        )
        
        self.db.add(dataset_file)
        await self.db.commit()
        await self.db.refresh(dataset_file)
        
        logger.info(f"Saved JSONL file to dataset: {file_name}")
        return dataset_file

    async def process_task(self, task_id: str) -> None:
        """执行QA生成任务 (后台任务)
        
        完整数据流程:
        1. 根据 file_ids 从 t_dm_dataset_files 读取指定的文件
        2. 对每个文件进行文本切片和QA生成（支持 .txt/.md/.json）
        3. 将QA对存入 t_qa_pairs 表
        4. 将每个源文件的QA对导出为对应的 .jsonl 文件（Alpaca格式）
        5. 将 .jsonl 文件保存到目标数据集的 t_dm_dataset_files
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

            # Step 1: 解析 source_dataset_id (实际存储的是 file_ids JSON数组)
            try:
                file_ids = json.loads(task.source_dataset_id)
            except:
                # 兼容旧版本（如果是单个 dataset_id 字符串）
                file_ids = [task.source_dataset_id]
            
            source_files = await self.get_source_files_by_ids(file_ids)
            if not source_files:
                raise ValueError(f"No supported files found from file_ids: {file_ids}")
            
            await self.update_task_progress(task_id, total_files=len(source_files))
            logger.info(f"Processing {len(source_files)} files (formats: txt/md/json)")

            # 创建文本切片器
            splitter = self.create_text_splitter(task.text_split_config)
            qa_config = task.qa_generation_config
            extra_prompt = qa_config.get("extra_prompt")  # 获取用户自定义提示词

            # 创建输出目录（保存在 generation 文件夹）
            output_dir = Path(__file__).parent.parent / "generated_data" / task_id
            output_dir.mkdir(parents=True, exist_ok=True)
            abs_output_dir = output_dir.resolve()
            logger.info(f"========================================")
            logger.info(f"📁 JSONL 输出目录: {abs_output_dir}")
            logger.info(f"📁 绝对路径: {os.path.abspath(str(output_dir))}")
            logger.info(f"========================================")

            # Step 2-5: 处理每个文件
            for file_idx, source_file in enumerate(source_files, start=1):
                try:
                    logger.info(f"Processing file {file_idx}/{len(source_files)}: {source_file.file_name}")
                    
                    # 读取文件内容（自动检测格式）
                    text_content = self.extract_text_from_file(source_file.file_path)
                    
                    # 文本切片
                    chunks = splitter.split_text(text_content)
                    logger.info(f"Split into {len(chunks)} chunks")
                    
                    # Step 3: 为每个切片生成QA对并保存到 t_qa_pairs
                    for chunk_idx, chunk in enumerate(chunks):
                        qa_pairs = self.generate_qa_for_chunk(
                            chunk=chunk,
                            llm_client=llm_client,
                            model=qa_config.get("model", "gpt-5-nano"),
                            max_questions=qa_config.get("max_questions", 3),
                            temperature=qa_config.get("temperature", 0.3),
                            extra_prompt=extra_prompt,  # 传入用户自定义提示词
                        )
                        logger.info(
                          f"[QA生成] 文件={source_file.file_name}, chunk={chunk_idx}, "
                          f"生成数量={len(qa_pairs)}, 示例={qa_pairs[0] if qa_pairs else 'None'}"
                        )

                        
                        # 保存每个QA对
                        for qa in qa_pairs:
                            await self.save_qa_pair(
                                task_id=task_id,
                                source_file_id=source_file.id,
                                source_file_name=source_file.file_name,
                                chunk_index=chunk_idx,
                                text_chunk=chunk,
                                question=qa.get("question", ""),
                                answer=qa.get("answer", ""),
                            )
                        
                        # 更新进度
                        await self.update_task_progress(
                            task_id,
                            processed_chunks=(await self.get_processed_chunks_count(task_id)),
                            total_qa_pairs=(await self.get_total_qa_pairs_count(task_id)),
                        )
                    
                    await self.db.commit()  # 提交该文件的所有QA对
                    logger.info(f"[文件处理] ✓ QA对已提交到数据库")
                    
                    # Step 4: 导出为 JSONL 文件 (abc.txt -> abc.jsonl)
                    base_name = Path(source_file.file_name).stem
                    jsonl_filename = f"{base_name}.jsonl"
                    jsonl_path = str(output_dir / jsonl_filename)
                    
                    logger.info(f"[文件处理] 准备导出JSONL: {jsonl_filename}")
                    logger.info(f"[文件处理] 完整路径: {os.path.abspath(jsonl_path)}")
                    
                    qa_count = await self.export_qa_pairs_to_jsonl(
                        task_id=task_id,
                        source_file_id=source_file.id,
                        output_path=jsonl_path,
                    )
                    
                    if qa_count == 0:
                        logger.error(f"[文件处理] ❌ 未导出任何QA对，跳过数据集保存")
                        continue
                    
                    logger.info(f"[文件处理] ✓ JSONL文件已生成: {qa_count} 条QA")
                    
                    # Step 5: 将 JSONL 文件保存到目标数据集
                    logger.info(f"[文件处理] 保存JSONL到目标数据集 (dataset_id={task.target_dataset_id})")
                    await self.save_jsonl_to_dataset(
                        dataset_id=task.target_dataset_id,
                        file_name=jsonl_filename,
                        file_path=jsonl_path,
                    )
                    logger.info(f"[文件处理] ✓ JSONL文件已保存到数据集")
                    
                    # 更新文件处理进度
                    await self.update_task_progress(task_id, processed_files=file_idx)
                    
                    logger.info(f"Completed processing file: {source_file.file_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to process file {source_file.file_name}: {e}")
                    continue

            # 更新任务状态为完成
            await self.update_task_status(task_id, "COMPLETED")
            logger.info(f"Task {task_id} completed successfully")

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            await self.update_task_status(task_id, "FAILED", str(e))
            raise

    async def get_processed_chunks_count(self, task_id: str) -> int:
        """获取已处理的文本块数量（按 chunk_index 去重）"""
        subquery = (
            select(QAPair.chunk_index)
            .where(QAPair.task_id == task_id)
            .distinct()
            .subquery()
        )

        result = await self.db.execute(
            select(func.count()).select_from(subquery)
        )
        return result.scalar_one()

    async def get_total_qa_pairs_count(self, task_id: str) -> int:
        """获取生成的QA对总数"""
        result = await self.db.execute(
            select(func.count()).select_from(QAPair)
            .where(QAPair.task_id == task_id)
        )
        return result.scalar_one()
