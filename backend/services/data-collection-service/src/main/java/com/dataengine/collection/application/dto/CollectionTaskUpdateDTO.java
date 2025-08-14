package com.dataengine.collection.application.dto;

import java.util.Map;

/**
 * 更新归集任务DTO
 */
public class CollectionTaskUpdateDTO {

    private String name;
    private String description;
    private Map<String, String> config;
    private String schedule;

    public CollectionTaskUpdateDTO() {}

    public CollectionTaskUpdateDTO(String name, String description, Map<String, String> config, String schedule) {
        this.name = name;
        this.description = description;
        this.config = config;
        this.schedule = schedule;
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

    public String getSchedule() {
        return schedule;
    }

    public void setSchedule(String schedule) {
        this.schedule = schedule;
    }
}
