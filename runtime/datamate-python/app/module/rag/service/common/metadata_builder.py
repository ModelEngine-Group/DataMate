"""
元数据构建工具

提供构建和管理分块元数据的工具方法。
"""
from typing import Dict, Any
from app.db.models.knowledge_gen import KnowledgeBase, RagFile


class MetadataBuilder:
    """元数据构建工具类"""
    
    @staticmethod
    def build_chunk_metadata(rag_file: RagFile, knowledge_base: KnowledgeBase) -> Dict[str, Any]:
        """构建分块基础元数据
        
        Args:
            rag_file: RAG 文件实体
            knowledge_base: 知识库实体
            
        Returns:
            元数据字典
        """
        return {
            "rag_file_id": str(rag_file.id),
            "original_file_id": str(rag_file.file_id),
            "knowledge_base_id": str(knowledge_base.id),
            "file_name": rag_file.file_name,
            "knowledge_base_name": knowledge_base.name,
        }
    
    @staticmethod
    def add_to_chunks(chunks: list, base_metadata: Dict[str, Any]) -> None:
        """为基础元数据添加到分块列表
        
        Args:
            chunks: 分块列表
            base_metadata: 基础元数据
        """
        for chunk in chunks:
            if hasattr(chunk, 'metadata') and isinstance(chunk.metadata, dict):
                chunk.metadata.update(base_metadata)
