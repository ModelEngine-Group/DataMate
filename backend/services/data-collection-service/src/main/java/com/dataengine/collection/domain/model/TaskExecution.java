package com.dataengine.collection.domain.model;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class TaskExecution {
    private String id;
    private String taskId;
    private String taskName;
    private ExecutionStatus status;
    private Double progress;
    private Long recordsTotal;
    private Long recordsProcessed;
    private Long recordsSuccess;
    private Long recordsFailed;
    private Double throughput;
    private Long dataSizeBytes;
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
    private Integer durationSeconds;
    private String errorMessage;
    private String dataxJobId;
    private String config;
    private String result;
    private LocalDateTime createdAt;
}
