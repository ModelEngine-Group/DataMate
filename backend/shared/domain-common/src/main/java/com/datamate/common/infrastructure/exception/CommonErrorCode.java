package com.datamate.common.infrastructure.exception;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * CommonErrorCode
 *
 * @since 2025/12/5
 */
@Getter
@AllArgsConstructor
public enum CommonErrorCode implements ErrorCode{
    PRE_UPLOAD_REQUEST_NOT_EXIST("common.0101", "预上传请求不存在"),
    PARAM_ERROR("common.0001", "参数错误");
    private final String code;
    private final String message;
}
