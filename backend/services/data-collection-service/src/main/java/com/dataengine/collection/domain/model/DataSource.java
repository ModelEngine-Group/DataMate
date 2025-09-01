package com.dataengine.collection.domain.model;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 数据源实体
 */
@Data
public class DataSource {
    private String id;
    private String name;
    private DataSourceType type;
    private String description;
    /**
     * 原始JSON字符串，入库到 JSON 列
     */
    private String config;
    private DataSourceStatus status;
    private LocalDateTime lastTestAt;
    private String lastTestResult; // JSON字符串
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private String createdBy;
    private String updatedBy;
}
