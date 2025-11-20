package com.datamate.rag.indexer.interfaces.dto;

/**
 * 分块处理类型
 *
 * @author dallas
 * @since 2025-10-29
 */
public enum ProcessType {
    /**
     * 段落分块
     */
    PARAGRAPH_CHUNK,

    /**
     * 按句子分块
     */
    SENTENCE_CHUNK,

    /**
     * 按长度分块，字符串分块
     */
    LENGTH_CHUNK,

    /**
     * 默认分块，按单词分块
     */
    DEFAULT_CHUNK,

    /**
     * 自定义分割符分块
     */
    CUSTOM_SEPARATOR_CHUNK,
}
