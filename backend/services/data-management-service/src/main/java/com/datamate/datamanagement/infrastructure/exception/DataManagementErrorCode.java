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
     * 数据集文件已存在
     */
    DATASET_FILE_ALREADY_EXISTS("data_management.0006", "数据集文件已存在"),
    /**
     * 目录不存在
     */
    DIRECTORY_NOT_FOUND("data_management.0007", "目录不存在"),
    /**
     * 数据集名称长度不能超过255个字符
     */
    DATASET_NAME_TOO_LONG("data_management.0008", "数据集名称长度不能超过255个字符"),
    /**
     * 数据集类型不合法
     */
    DATASET_TYPE_INVALID("data_management.0009", "数据集类型不合法"),
    /**
     * 数据集状态不合法
     */
    DATASET_STATUS_INVALID("data_management.0010", "数据集状态不合法"),
    /**
     * 标签名称长度不能超过100个字符
     */
    TAG_NAME_TOO_LONG("data_management.0011", "标签名称长度不能超过100个字符"),
    /**
     * 标签名称已存在
     */
    TAG_NAME_DUPLICATE("data_management.0012", "标签名称已存在"),
    /**
     * 标签颜色格式不正确，应为十六进制颜色代码
     */
    TAG_COLOR_INVALID("data_management.0013", "标签颜色格式不正确，应为十六进制颜色代码"),
    /**
     * 保留天数必须为非负整数
     */
    RETENTION_DAYS_INVALID("data_management.0014", "保留天数必须为非负整数"),
    /**
     * 路径长度不能超过限制
     */
    PATH_TOO_LONG("data_management.0015", "路径长度不能超过限制"),
    /**
     * 文件名包含非法字符
     */
    FILE_NAME_INVALID("data_management.0016", "文件名包含非法字符"),
    /**
     * 路径前缀不能以点开头
     */
    PREFIX_INVALID("data_management.0017", "路径前缀不能以点开头");

    private final String code;
    private final String message;
}
