"""
批量处理工具

提供分批处理文档分块的工具方法。
"""
import uuid
import logging
from typing import List
from app.module.rag.infra.vectorstore import chunks_to_documents
from app.module.rag.infra.document.types import DocumentChunk


logger = logging.getLogger(__name__)


class BatchProcessor:
    """批量处理工具类"""
    
    DEFAULT_BATCH_SIZE: int = 20
    
    @staticmethod
    async def store_in_batches(
        vectorstore,
        chunks: List[DocumentChunk],
        batch_size: int = DEFAULT_BATCH_SIZE
    ) -> int:
        """分批存储分块到向量数据库
        
        Args:
            vectorstore: 向量存储实例
            chunks: 分块列表
            batch_size: 批次大小
            
        Returns:
            成功存储的分块数量
        """
        if not chunks:
            return 0
        
        batch_size = batch_size or BatchProcessor.DEFAULT_BATCH_SIZE
        total_chunks = len(chunks)
        stored_count = 0
        
        for batch_start in range(0, total_chunks, batch_size):
            batch_end = min(batch_start + batch_size, total_chunks)
            batch_chunks = chunks[batch_start:batch_end]
            
            await BatchProcessor._store_single_batch(
                vectorstore,
                batch_chunks,
                batch_start,
                batch_end,
                total_chunks
            )
            stored_count += len(batch_chunks)
        
        logger.info("批量存储完成，总数量: %d", stored_count)
        return stored_count
    
    @staticmethod
    async def _store_single_batch(
        vectorstore,
        batch_chunks: List[DocumentChunk],
        batch_start: int,
        batch_end: int,
        total_chunks: int,
    ) -> None:
        """存储单个批次
        
        Args:
            vectorstore: 向量存储实例
            batch_chunks: 批次分块列表
            batch_start: 批次起始索引
            batch_end: 批次结束索引
            total_chunks: 总分块数
        """
        logger.info("处理分块批次 %d-%d / %d", batch_start + 1, batch_end, total_chunks)
        
        ids = [str(uuid.uuid4()) for _ in batch_chunks]
        documents, doc_ids = chunks_to_documents(batch_chunks, ids=ids)
        
        try:
            # 使用异步方法避免阻塞事件循环
            await vectorstore.aadd_documents(documents=documents, ids=doc_ids)
            logger.info("批次 %d-%d 存储成功", batch_start + 1, batch_end)
        except Exception as e:
            logger.error(
                "批次 %d-%d 存储失败: %s\n第一个文档内容: %.200s",
                batch_start + 1,
                batch_end,
                str(e),
                documents[0].page_content if documents else "N/A"
            )
            raise
