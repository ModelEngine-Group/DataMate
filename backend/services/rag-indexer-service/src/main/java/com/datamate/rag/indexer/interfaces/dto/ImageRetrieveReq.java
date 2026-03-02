package com.datamate.rag.indexer.interfaces.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.List;

/**
 * 图片检索请求
 *
 * @author datamate
 * @since 2025-02-28
 */
@Data
public class ImageRetrieveReq {
    
    /**
     * 图片 URL 或本地文件路径
     */
    @NotBlank(message = "图片地址不能为空")
    private String imageUrl;
    
    /**
     * 附加文本描述（可选）
     */
    private String queryText;
    
    /**
     * 返回结果数量
     */
    @NotNull
    private Integer topK = 10;
    
    /**
     * 知识库 ID 列表（目前只支持单个知识库）
     */
    @NotNull(message = "知识库 ID 不能为空")
    private List<@NotBlank String> knowledgeBaseIds;
}
