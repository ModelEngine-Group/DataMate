"""
RAG 模块枚举定义

包含所有 RAG 相关的枚举类型，与 Java 枚举保持一致
从 app.db.models.knowledge_gen 导入以避免循环依赖
"""
from enum import Enum

# 从模型导入以避免循环依赖


class ProcessType(str, Enum):
    """分块处理类型枚举

    对应 Java: com.datamate.rag.indexer.interfaces.dto.ProcessType
    """
    PARAGRAPH_CHUNK = "PARAGRAPH_CHUNK"           # 段落分块
    SENTENCE_CHUNK = "SENTENCE_CHUNK"             # 按句子分块
    LENGTH_CHUNK = "LENGTH_CHUNK"                 # 按长度分块（字符）
    DEFAULT_CHUNK = "DEFAULT_CHUNK"               # 默认分块（单词）
    CUSTOM_SEPARATOR_CHUNK = "CUSTOM_SEPARATOR_CHUNK"  # 自定义分隔符分块
