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
    PARAM_ERROR("common.0001", "参数错误"),
    PRE_UPLOAD_REQUEST_NOT_EXIST("common.0101", "预上传请求不存在"),
    SIGNUP_ERROR("common.0400", "用户名或者邮箱已经存在"),
    UNAUTHORIZED("common.0401", "认证失败");
    private final String code;
    private final String message;
}
