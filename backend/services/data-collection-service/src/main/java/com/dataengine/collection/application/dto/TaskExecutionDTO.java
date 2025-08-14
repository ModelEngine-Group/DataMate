package com.dataengine.collection.application.dto;

import java.time.LocalDateTime;

/**
 * 任务执行记录DTO
 */
public class TaskExecutionDTO {

    private String id;
    private String taskId;
    private String status;
    private LocalDateTime startTime;
    private LocalDateTime endTime;
    private Long duration;
    private Long processedRecords;
    private String errorMessage;
    private String executionLogs;

    public TaskExecutionDTO() {}

    public TaskExecutionDTO(String id, String taskId, String status, LocalDateTime startTime,
                          LocalDateTime endTime, Long duration, Long processedRecords,
                          String errorMessage, String executionLogs) {
        this.id = id;
        this.taskId = taskId;
        this.status = status;
        this.startTime = startTime;
        this.endTime = endTime;
        this.duration = duration;
        this.processedRecords = processedRecords;
        this.errorMessage = errorMessage;
        this.executionLogs = executionLogs;
    }

    // Getters and Setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getTaskId() {
        return taskId;
    }

    public void setTaskId(String taskId) {
        this.taskId = taskId;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public LocalDateTime getStartTime() {
        return startTime;
    }

    public void setStartTime(LocalDateTime startTime) {
        this.startTime = startTime;
    }

    public LocalDateTime getEndTime() {
        return endTime;
    }

    public void setEndTime(LocalDateTime endTime) {
        this.endTime = endTime;
    }

    public Long getDuration() {
        return duration;
    }

    public void setDuration(Long duration) {
        this.duration = duration;
    }

    public Long getProcessedRecords() {
        return processedRecords;
    }

    public void setProcessedRecords(Long processedRecords) {
        this.processedRecords = processedRecords;
    }

    public String getErrorMessage() {
        return errorMessage;
    }

    public void setErrorMessage(String errorMessage) {
        this.errorMessage = errorMessage;
    }

    public String getExecutionLogs() {
        return executionLogs;
    }

    public void setExecutionLogs(String executionLogs) {
        this.executionLogs = executionLogs;
    }
}
