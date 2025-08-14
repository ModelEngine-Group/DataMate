package com.dataengine.collection.application.dto;

import com.dataengine.collection.domain.model.DataSourceType;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.util.Map;

/**
 * 创建数据源DTO
 */
public class DataSourceCreateDTO {

    @NotBlank(message = "数据源名称不能为空")
    private String name;

    @NotNull(message = "数据源类型不能为空")
    private DataSourceType type;

    private String description;

    @NotNull(message = "数据源配置不能为空")
    private Map<String, String> config;

    public DataSourceCreateDTO() {}

    public DataSourceCreateDTO(String name, DataSourceType type, String description, Map<String, String> config) {
        this.name = name;
        this.type = type;
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
}
