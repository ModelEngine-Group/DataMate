package com.datamate.rag.indexer.interfaces.dto;

import com.datamate.common.setting.domain.entity.ModelConfig;
import com.datamate.rag.indexer.domain.model.KnowledgeBase;
import lombok.Getter;
import lombok.Setter;

/**
 * 知识库响应实体
 *
 * @author dallas
 * @since 2025-11-17
 */
@Setter
@Getter
public class KnowledgeBaseResp extends KnowledgeBase {
    private Long fileCount;
    private Long chunkCount;
    private ModelConfig embedding;
    private ModelConfig chat;
}