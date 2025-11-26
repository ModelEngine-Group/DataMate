package com.datamate.rag.indexer.interfaces.dto;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

/**
 * 知识库创建请求
 *
 * @author dallas
 * @since 2025-10-24
 */
@Setter
@Getter
public class KnowledgeBaseCreateReq {
    /**
     * 知识库名称
     */
    @NotEmpty(message = "知识库名称不能为空")
    @Size(min = 1, max = 255, message = "知识库名称长度必须在 1 到 255 之间")
    @Pattern(regexp = "^[a-zA-Z][a-zA-Z0-9_]*$", message = "知识库名称只能包含字母、数字和下划线")
    private String name;
    /**
     * 知识库描述
     */
    @Size(max = 512, message = "知识库描述长度必须在 0 到 512 之间")
    private String description;

    /**
     * 嵌入模型
     */
    @NotEmpty(message = "嵌入模型不能为空")
    private String embeddingModel;

    /**
     * 聊天模型
     */
    private String chatModel;
}
