package com.dataengine.collection.domain.model;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class TaskSchedule {
    private String id;
    private String taskId;
    private String cronExpression;
    private String timezone;
    private Boolean enabled;
    private LocalDateTime nextExecutionTime;
    private LocalDateTime lastExecutionTime;
    private Long executionCount;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
