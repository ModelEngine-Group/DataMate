package com.dataengine.collection.domain.model;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class CollectionTask {
    private String id;
    private String name;
    private String description;
    private String sourceDataSourceId;
    private String targetDataSourceId;
    private String config; // DataX JSON 配置
    private TaskStatus status;
    private String scheduleExpression;
    private Integer retryCount;
    private Integer timeoutSeconds;
    private Long maxRecords;
    private String sortField;
    private String lastExecutionId;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private String createdBy;
    private String updatedBy;
}
