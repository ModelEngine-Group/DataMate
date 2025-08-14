package com.dataengine.collection.application.dto;

import java.util.Map;

/**
 * 更新数据源DTO
 */
public class DataSourceUpdateDTO {

    private String name;
    private String description;
    private Map<String, String> config;

    public DataSourceUpdateDTO() {}

    public DataSourceUpdateDTO(String name, String description, Map<String, String> config) {
        this.name = name;
        this.description = description;
        this.config = config;
    }

    // Getters and Setters
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

    public Map<String, String> getConfig() {
        return config;
    }

    public void setConfig(Map<String, String> config) {
        this.config = config;
    }
}
