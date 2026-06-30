package com.datamate.common.infrastructure.exception;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 系统错误码枚举
 *
 * @author dallas
 * @since 2025-10-17
 */
@Getter
@AllArgsConstructor
public enum SystemErrorCode implements ErrorCode {
    /**
     * 未知错误
     */
    UNKNOWN_ERROR("sys.0001", "未知错误"),
    /**
     * 系统繁忙，请稍后重试
     */
    SYSTEM_BUSY("sys.0002", "系统繁忙，请稍后重试"),
    /**
     * 参数错误
     */
    INVALID_PARAMETER("sys.0003", "参数错误"),
    /**
     * 资源未找到
     */
    RESOURCE_NOT_FOUND("sys.0004", "资源未找到"),
    /**
     * 权限不足
     */
    INSUFFICIENT_PERMISSIONS("sys.0005", "权限不足"),

    /**
     * 文件系统错误
     */
    FILE_SYSTEM_ERROR("sys.0006", "文件系统错误");

    private final String code;
    private final String message;
}
