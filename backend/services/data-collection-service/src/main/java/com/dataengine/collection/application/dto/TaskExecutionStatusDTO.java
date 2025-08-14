package com.dataengine.collection.application.dto;

/**
 * 任务执行状态DTO
 */
public class TaskExecutionStatusDTO {

    private String taskId;
    private String status;
    private String message;
    private Double progress;
    private Long processedRecords;
    private Long totalRecords;
    private String currentPhase;

    public TaskExecutionStatusDTO() {}

    public TaskExecutionStatusDTO(String taskId, String status, String message, Double progress,
                                Long processedRecords, Long totalRecords, String currentPhase) {
        this.taskId = taskId;
        this.status = status;
        this.message = message;
        this.progress = progress;
        this.processedRecords = processedRecords;
        this.totalRecords = totalRecords;
        this.currentPhase = currentPhase;
    }

    // Getters and Setters
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

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public Double getProgress() {
        return progress;
    }

    public void setProgress(Double progress) {
        this.progress = progress;
    }

    public Long getProcessedRecords() {
        return processedRecords;
    }

    public void setProcessedRecords(Long processedRecords) {
        this.processedRecords = processedRecords;
    }

    public Long getTotalRecords() {
        return totalRecords;
    }

    public void setTotalRecords(Long totalRecords) {
        this.totalRecords = totalRecords;
    }

    public String getCurrentPhase() {
        return currentPhase;
    }

    public void setCurrentPhase(String currentPhase) {
        this.currentPhase = currentPhase;
    }
}
