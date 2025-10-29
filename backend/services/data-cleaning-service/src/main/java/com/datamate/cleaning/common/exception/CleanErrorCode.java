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

    CREATE_DATASET_FAILED("clean.0002", "创建数据集失败");

    private final String code;
    private final String message;
}
