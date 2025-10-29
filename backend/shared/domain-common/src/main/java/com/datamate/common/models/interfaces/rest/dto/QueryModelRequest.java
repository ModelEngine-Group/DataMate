package com.datamate.common.models.interfaces.rest.dto;

import com.datamate.common.interfaces.PagingQuery;
import com.datamate.common.models.domain.entity.ModelType;
import lombok.Getter;
import lombok.Setter;

/**
 * 模型查询请求 DTO
 *
 * @author dallas
 * @since 2025-10-27
 */
@Getter
@Setter
public class QueryModelRequest extends PagingQuery {
    /**
     * 模型提供商（如 Ollama、OpenAI、DeepSeek）
     */
    private String provider;
     /**
      * 模型类型（如 chat、embedding）
      */
    private ModelType type;

    private Boolean isEnabled;
}
