package com.datamate.rag.indexer.domain.model;

/**
 * RAG 文档块实体类
 *
 * @author dallas
 * @since 2025-10-29
 */

public record RagChunk(
        String id,
        String text,
        String metadata
) {
}