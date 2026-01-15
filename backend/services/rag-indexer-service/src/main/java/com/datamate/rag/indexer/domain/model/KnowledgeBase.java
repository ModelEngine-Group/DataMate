package com.datamate.rag.indexer.domain.model;

import com.baomidou.mybatisplus.annotation.TableName;
import com.datamate.common.domain.model.base.BaseEntity;
import com.datamate.rag.indexer.interfaces.dto.RagType;
import lombok.Getter;
import lombok.Setter;

/**
 * 知识库实体类
 *
 * @author dallas
 * @since 2025-10-24
 */
@Getter
@Setter
@TableName("t_rag_knowledge_base")
public class KnowledgeBase extends BaseEntity<String> {
    /**
     * 知识库名称
     */
    private String name;

    /**
     * 知识库描述
     */
    private String description;

    /**
     * RAG 类型
     */
    private RagType type;

    /**
     * 嵌入模型
     */
    private String embeddingModel;

    /**
     * 聊天模型
     */
    private String chatModel;
}
