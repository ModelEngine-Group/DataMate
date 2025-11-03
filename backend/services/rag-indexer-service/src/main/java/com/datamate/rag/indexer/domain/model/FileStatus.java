package com.datamate.rag.indexer.domain.model;

/**
 * 文件状态枚举
 *
 * @author dallas
 * @since 2025-10-29
 */
public enum FileStatus {
    /**
     * 未处理
     */
    UNPROCESSED,
    /**
     * 处理中
     */
    PROCESSING,
    /**
     * 已处理
     */
    PROCESSED,
    /**
     * 处理失败
     */
    PROCESS_FAILED
}
