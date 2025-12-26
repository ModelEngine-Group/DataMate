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

    FIELD_NOT_FOUND("op.0003", "缺少必要的字段"),

    SETTINGS_PARSE_FAILED("op.0004", "settings字段解析失败"),

    OPERATOR_IN_INSTANCE("op.0005", "算子已被编排在模板或未完成的任务中"),

    CANT_DELETE_PREDEFINED_OPERATOR("op.0006", "预置算子无法删除");

    private final String code;
    private final String message;
}
