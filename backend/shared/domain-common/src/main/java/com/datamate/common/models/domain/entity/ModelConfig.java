package com.datamate.common.models.domain.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import com.datamate.common.domain.model.base.BaseEntity;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;
import lombok.ToString;

/**
 * 模型配置实体类
 *
 * @author dallas
 * @since 2025-10-27
 */
@Getter
@Setter
@TableName("t_model_config")
@Builder
@ToString
public class ModelConfig extends BaseEntity<String> {
    /**
     * 模型名称（如 qwen2）
     */
    private String modelName;
    /**
     * 模型提供商（如 Ollama、OpenAI、DeepSeek）
     */
    private String provider;
    /**
     * API 基础地址
     */
    private String baseUrl;
    /**
     * API 密钥（无密钥则为空）
     */
    private String apiKey;
    /**
     * 模型类型（如 chat、embedding）
     */
    private ModelType type;
     /**
     * 是否启用：1-启用，0-禁用
     */
    private Boolean isEnabled;
}
