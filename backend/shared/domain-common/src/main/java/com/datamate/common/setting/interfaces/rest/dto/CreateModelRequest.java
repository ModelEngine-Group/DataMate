package com.datamate.common.setting.interfaces.rest.dto;

import com.datamate.common.setting.domain.entity.ModelType;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

/**
 * 创建模型配置请求类
 *
 * @author dallas
 * @since 2025-10-27
 */
@Setter
@Getter
public class CreateModelRequest {
    /**
     * 模型名称（如 qwen2）
     */
    @NotEmpty(message = "模型名称不能为空")
    private String modelName;
    /**
     * 模型提供商（如 Ollama、OpenAI、DeepSeek）
     */
    @NotEmpty(message = "模型提供商不能为空")
    private String provider;
    /**
     * API 基础地址
     */
    @NotEmpty(message = "API 基础地址不能为空")
    private String baseUrl;
    /**
     * API 密钥（无密钥则为空）
     */
    private String apiKey;
    /**
     * 模型类型（如 chat、embedding）
     */
    @NotNull(message = "模型类型不能为空")
    private ModelType type;
    /**
     * 是否启用：1-启用，0-禁用
     */
    private Boolean isEnabled;
}
