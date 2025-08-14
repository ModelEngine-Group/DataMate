package com.dataengine.collection.domain.model;

/**
 * 数据源状态枚举
 */
public enum DataSourceStatus {
    INACTIVE("未激活"),
    ACTIVE("已激活"),
    ERROR("连接错误"),
    TESTING("连接测试中");

    private final String description;

    DataSourceStatus(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }

    public boolean canBeUsed() {
        return this == ACTIVE;
    }
}
