package com.datamate.common.infrastructure.exception;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 知识库错误码
 *
 * @author dallas
 * @since 2025-10-24
 */

@Getter
@AllArgsConstructor
public enum KnowledgeBaseErrorCode implements ErrorCode {
    /**
     * 知识库不存在
     */
    KNOWLEDGE_BASE_NOT_FOUND("knowledge.0001", "知识库不存在"),

    /**
     * 文件不存在
     */
    RAG_FILE_NOT_FOUND("knowledge.0002", "文件不存在");

    private final String code;
    private final String message;
}
