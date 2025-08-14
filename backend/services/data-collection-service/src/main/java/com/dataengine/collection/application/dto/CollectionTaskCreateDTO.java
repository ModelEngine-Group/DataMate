package com.dataengine.collection.application.dto;

import com.dataengine.collection.domain.model.TaskStatus;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.util.Map;

/**
 * 创建归集任务DTO
 */
public class CollectionTaskCreateDTO {

    @NotBlank(message = "任务名称不能为空")
    private String name;

    private String description;

    @NotBlank(message = "源数据源ID不能为空")
    private String sourceDataSourceId;

    @NotBlank(message = "目标数据源ID不能为空")
    private String targetDataSourceId;

    @NotNull(message = "任务配置不能为空")
    private Map<String, String> config;

    private String schedule;

    public CollectionTaskCreateDTO() {}

    public CollectionTaskCreateDTO(String name, String description, String sourceDataSourceId,
                                 String targetDataSourceId, Map<String, String> config, String schedule) {
        this.name = name;
        this.description = description;
        this.sourceDataSourceId = sourceDataSourceId;
        this.targetDataSourceId = targetDataSourceId;
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

    public String getSourceDataSourceId() {
        return sourceDataSourceId;
    }

    public void setSourceDataSourceId(String sourceDataSourceId) {
        this.sourceDataSourceId = sourceDataSourceId;
    }

    public String getTargetDataSourceId() {
        return targetDataSourceId;
    }

    public void setTargetDataSourceId(String targetDataSourceId) {
        this.targetDataSourceId = targetDataSourceId;
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
