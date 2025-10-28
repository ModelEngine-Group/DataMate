package com.datamate.common.models.infrastructure.exception;

import com.datamate.common.infrastructure.exception.ErrorCode;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 模型配置错误码枚举类
 *
 * @author dallas
 * @since 2025-10-27
 */
@Getter
@AllArgsConstructor
public enum ModelsErrorCode implements ErrorCode {
    /**
     * 模型配置不存在
     */
    MODEL_CONFIG_NOT_FOUND("model.0001", "模型配置不存在"),
    /**
     * 模型配置已存在
     */
    MODEL_CONFIG_ALREADY_EXISTS("model.0002", "模型配置已存在"),

    /**
     * 模型健康检查失败
     */
    MODEL_HEALTH_CHECK_FAILED("model.0003", "模型健康检查失败");

    private final String code;
    private final String message;
}
