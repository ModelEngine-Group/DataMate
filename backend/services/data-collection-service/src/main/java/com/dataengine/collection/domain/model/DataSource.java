package com.dataengine.collection.domain.model;

import com.dataengine.shared.domain.AggregateRoot;
import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.Map;

/**
 * 数据源聚合根
 * 
 * 管理各种类型的数据源连接配置信息
 */
@Entity
@Table(name = "collection_data_sources")
public class DataSource extends AggregateRoot<DataSourceId> {

    @EmbeddedId
    private DataSourceId id;

    @Column(nullable = false)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private DataSourceType type;

    private String description;

    @ElementCollection
    @CollectionTable(name = "data_source_configs")
    @MapKeyColumn(name = "config_key")
    @Column(name = "config_value")
    private Map<String, String> config;

    @Enumerated(EnumType.STRING)
    private DataSourceStatus status;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    protected DataSource() {
        super();
        // JPA constructor
    }

    public DataSource(DataSourceId id, String name, DataSourceType type, 
                     String description, Map<String, String> config) {
        super(id);
        this.id = id;
        this.name = name;
        this.type = type;
        this.description = description;
        this.config = config;
        this.status = DataSourceStatus.INACTIVE;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    public void updateConfig(Map<String, String> newConfig) {
        this.config.clear();
        this.config.putAll(newConfig);
        this.updatedAt = LocalDateTime.now();
    }

    public void activate() {
        this.status = DataSourceStatus.ACTIVE;
        this.updatedAt = LocalDateTime.now();
    }

    public void deactivate() {
        this.status = DataSourceStatus.INACTIVE;
        this.updatedAt = LocalDateTime.now();
    }

    public boolean isActive() {
        return this.status == DataSourceStatus.ACTIVE;
    }

    // Getters
    @Override
    public DataSourceId getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public DataSourceType getType() {
        return type;
    }

    public String getDescription() {
        return description;
    }

    public Map<String, String> getConfig() {
        return config;
    }

    public DataSourceStatus getStatus() {
        return status;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }
}
