package com.datamate.common.infrastructure.exception;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

/**
 * 业务异常基类
 *
 * @author dallas
 * @since 2025-10-15
 */
public class BusinessException extends RuntimeException {
    private final ErrorCode errorCode;
    private final Map<String, Object> details;

    // 核心构造方法
    private BusinessException(ErrorCode errorCode, String customMessage,
                              Map<String, Object> details, Throwable cause) {
        super(customMessage != null ? customMessage : errorCode.getMessage(), cause);
        this.errorCode = errorCode;
        this.details = details != null ? new HashMap<>(details) : new HashMap<>();
    }

    // 静态工厂方法
    public static BusinessException of(ErrorCode errorCode) {
        return new BusinessException(errorCode, null, null, null);
    }

    public static BusinessException of(ErrorCode errorCode, String customMessage) {
        return new BusinessException(errorCode, customMessage, null, null);
    }

    public static BusinessException of(ErrorCode errorCode, Map<String, Object> details) {
        return new BusinessException(errorCode, null, details, null);
    }

    public static BusinessException of(ErrorCode errorCode, String customMessage,
                                       Map<String, Object> details) {
        return new BusinessException(errorCode, customMessage, details, null);
    }

    // 快速创建方法 - 支持链式调用添加详情
    public static BusinessException create(ErrorCode errorCode) {
        return new BusinessException(errorCode, null, null, null);
    }

    public BusinessException withDetail(String key, Object value) {
        this.details.put(key, value);
        return this;
    }

    public BusinessException withCustomMessage(String customMessage) {
        return new BusinessException(this.errorCode, customMessage, this.details, null);
    }

    // Getter方法
    public String getCode() {
        return errorCode.getCode();
    }

    public ErrorCode getErrorCodeEnum() {
        return errorCode;
    }

    public Map<String, Object> getDetails() {
        return Collections.unmodifiableMap(details);
    }

    public String getOriginalMessage() {
        return errorCode.getMessage();
    }
}
