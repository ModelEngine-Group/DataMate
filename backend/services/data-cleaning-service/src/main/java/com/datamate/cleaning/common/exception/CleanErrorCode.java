package com.datamate.cleaning.common.exception;

import com.datamate.common.infrastructure.exception.ErrorCode;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public enum CleanErrorCode implements ErrorCode {
    /**
     * 清洗任务名称重复
     */
    DUPLICATE_TASK_NAME("clean.0001", "清洗任务名称重复"),

    OPERATOR_LIST_EMPTY("clean.0002", "任务列表为空"),

    IN_AND_OUT_NOT_MATCH("clean.0003", "算子输入输出不匹配"),

    EXECUTOR_NOT_MATCH("clean.0004", "算子执行器不匹配");

    private final String code;
    private final String message;
}
