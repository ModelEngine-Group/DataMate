package com.dataengine.collection.application.dto;

import com.dataengine.collection.domain.model.TaskStatus;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 归集任务响应DTO
 */
public class CollectionTaskDTO {

    private String id;
    private String name;
    private String description;
    private String sourceDataSourceId;
    private String sourceDataSourceName;
    private String targetDataSourceId;
    private String targetDataSourceName;
    private Map<String, String> config;
    private TaskStatus status;
    private String schedule;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public CollectionTaskDTO() {}

    public CollectionTaskDTO(String id, String name, String description, String sourceDataSourceId,
                           String sourceDataSourceName, String targetDataSourceId, String targetDataSourceName,
                           Map<String, String> config, TaskStatus status, String schedule,
                           LocalDateTime createdAt, LocalDateTime updatedAt) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.sourceDataSourceId = sourceDataSourceId;
        this.sourceDataSourceName = sourceDataSourceName;
        this.targetDataSourceId = targetDataSourceId;
        this.targetDataSourceName = targetDataSourceName;
        this.config = config;
        this.status = status;
        this.schedule = schedule;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    // Getters and Setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getSourceDataSourceId() {
        return sourceDataSourceId;
    }

    public void setSourceDataSourceId(String sourceDataSourceId) {
        this.sourceDataSourceId = sourceDataSourceId;
    }

    public String getSourceDataSourceName() {
        return sourceDataSourceName;
    }

    public void setSourceDataSourceName(String sourceDataSourceName) {
        this.sourceDataSourceName = sourceDataSourceName;
    }

    public String getTargetDataSourceId() {
        return targetDataSourceId;
    }

    public void setTargetDataSourceId(String targetDataSourceId) {
        this.targetDataSourceId = targetDataSourceId;
    }

    public String getTargetDataSourceName() {
        return targetDataSourceName;
    }

    public void setTargetDataSourceName(String targetDataSourceName) {
        this.targetDataSourceName = targetDataSourceName;
    }

    public Map<String, String> getConfig() {
        return config;
    }

    public void setConfig(Map<String, String> config) {
        this.config = config;
    }

    public TaskStatus getStatus() {
        return status;
    }

    public void setStatus(TaskStatus status) {
        this.status = status;
    }

    public String getSchedule() {
        return schedule;
    }

    public void setSchedule(String schedule) {
        this.schedule = schedule;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }
}
