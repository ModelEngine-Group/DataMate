package com.dataengine.collection.domain.model;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class CollectionTask {
    private String id;
    private String name;
    private String description;
    private String config; // DataX JSON 配置，包含源端和目标端配置信息
    private TaskStatus status;
    private String syncMode; // ONCE / SCHEDULED
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
