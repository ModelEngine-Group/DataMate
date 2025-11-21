package com.datamate.datamanagement.infrastructure.exception;

import com.datamate.common.infrastructure.exception.ErrorCode;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 数据管理模块错误码
 *
 * @author dallas
 * @since 2025-10-20
 */
@Getter
@AllArgsConstructor
public enum DataManagementErrorCode implements ErrorCode {
    /**
     * 数据集不存在
     */
    DATASET_NOT_FOUND("data_management.0001", "数据集不存在"),
    /**
     * 数据集已存在
     */
    DATASET_ALREADY_EXISTS("data_management.0002", "数据集已存在"),
    /**
     * 数据集状态错误
     */
    DATASET_STATUS_ERROR("data_management.0003", "数据集状态错误"),
    /**
     * 数据集标签不存在
     */
    DATASET_TAG_NOT_FOUND("data_management.0004", "数据集标签不存在"),
    /**
     * 数据集标签已存在
     */
    DATASET_TAG_ALREADY_EXISTS("data_management.0005", "数据集标签已存在"),
    /**
     * 数据集标签已存在
     */
    DATASET_FILE_ALREADY_EXISTS("data_management.0006", "数据集文件已存在");

    private final String code;
    private final String message;
}
