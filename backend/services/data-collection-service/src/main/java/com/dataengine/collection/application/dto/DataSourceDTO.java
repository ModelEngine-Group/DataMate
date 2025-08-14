package com.dataengine.collection.application.dto;

import com.dataengine.collection.domain.model.DataSourceType;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 数据源响应DTO
 */
public class DataSourceDTO {

    private String id;
    private String name;
    private DataSourceType type;
    private String description;
    private Map<String, String> config;
    private String status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public DataSourceDTO() {}

    public DataSourceDTO(String id, String name, DataSourceType type, String description,
                        Map<String, String> config, String status, LocalDateTime createdAt, LocalDateTime updatedAt) {
        this.id = id;
        this.name = name;
        this.type = type;
        this.description = description;
        this.config = config;
        this.status = status;
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

    public DataSourceType getType() {
        return type;
    }

    public void setType(DataSourceType type) {
        this.type = type;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public Map<String, String> getConfig() {
        return config;
    }

    public void setConfig(Map<String, String> config) {
        this.config = config;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
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
