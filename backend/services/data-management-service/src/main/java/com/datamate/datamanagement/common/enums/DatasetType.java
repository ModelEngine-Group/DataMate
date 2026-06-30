package com.datamate.datamanagement.common.enums;

import lombok.Getter;

/**
 * 数据集类型值对象
 *
 * @author DataMate
 * @since 2025-10-15
 */
public enum DatasetType {
    TEXT("text", "文本数据集"),
    IMAGE("image", "图像数据集"),
    AUDIO("audio", "音频数据集"),
    VIDEO("video", "视频数据集"),
    OTHER("other", "其他数据集");

    @Getter
    private final String code;

    @Getter
    private final String description;

    DatasetType(String code, String description) {
        this.code = code;
        this.description = description;
    }
}
