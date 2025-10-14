package com.dataengine.datamanagement.infrastructure.client.dto;

import lombok.Data;
import java.time.LocalDateTime;
import java.util.Map;

/**
 * 归集任务详情响应
 */
@Data
public class CollectionTaskDetailResponse {
    private String id;
    private String name;
    private String description;
    private Map<String, Object> config;
    private String status;
    private String syncMode;
    private String scheduleExpression;
    private String lastExecutionId;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
