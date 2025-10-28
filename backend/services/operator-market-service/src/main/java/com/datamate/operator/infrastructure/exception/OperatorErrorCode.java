package com.datamate.operator.infrastructure.exception;

import com.datamate.common.infrastructure.exception.ErrorCode;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public enum OperatorErrorCode implements ErrorCode {
    /**
     * 不支持的文件类型
     */
    UNSUPPORTED_FILE_TYPE("op.0001", "不支持的文件类型"),

    YAML_NOT_FOUND("op.0002", "算子中缺少元数据文件"),

    FIELD_NOT_FOUND("op.0003", "缺少必要的字段");

    private final String code;
    private final String message;
}
