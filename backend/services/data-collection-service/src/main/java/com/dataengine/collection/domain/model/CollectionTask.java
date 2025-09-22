package com.dataengine.collection.domain.model;

import com.dataengine.shared.domain.AggregateRoot;
import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.Map;

/**
 * 数据归集任务聚合根
 *
 * 定义数据从源数据源归集到目标数据源的任务配置
 */
@Entity
@Table(name = "collection_tasks")
public class CollectionTask extends AggregateRoot<CollectionTaskId> {

    @EmbeddedId
    private CollectionTaskId collectionTaskId;

    @Column(nullable = false)
    private String name;

    private String description;

    @Embedded
    @AttributeOverride(name = "value", column = @Column(name = "source_datasource_id"))
    private DataSourceId sourceDataSourceId;

    @Embedded
    @AttributeOverride(name = "value", column = @Column(name = "target_datasource_id"))
    private DataSourceId targetDataSourceId;

    @ElementCollection
    @CollectionTable(name = "collection_task_configs")
    @MapKeyColumn(name = "config_key")
    @Column(name = "config_value")
    private Map<String, String> config;

    @Enumerated(EnumType.STRING)
    private TaskStatus status;

    @Column(name = "schedule_expression")
    private String scheduleExpression;

    @Column(name = "last_execution_id")
    private String lastExecutionId;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    protected CollectionTask() {
        super();
        // JPA constructor
    }

    public CollectionTask(CollectionTaskId id, String name, String description,
                         DataSourceId sourceDataSourceId, DataSourceId targetDataSourceId,
                         Map<String, String> config, String scheduleExpression) {
        super(id);
        this.name = name;
        this.description = description;
        this.sourceDataSourceId = sourceDataSourceId;
        this.targetDataSourceId = targetDataSourceId;
        this.config = config;
        this.scheduleExpression = scheduleExpression;
        this.status = TaskStatus.DRAFT;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    public void updateConfig(Map<String, String> newConfig) {
        this.config.clear();
        this.config.putAll(newConfig);
        this.updatedAt = LocalDateTime.now();
    }

    public void updateSchedule(String scheduleExpression) {
        this.scheduleExpression = scheduleExpression;
        this.updatedAt = LocalDateTime.now();
    }

    public void ready() {
        if (this.status != TaskStatus.DRAFT) {
            throw new IllegalStateException("Only draft tasks can be set to ready");
        }
        this.status = TaskStatus.READY;
        this.updatedAt = LocalDateTime.now();
    }

    public void start(String executionId) {
        if (this.status != TaskStatus.READY && this.status != TaskStatus.COMPLETED
            && this.status != TaskStatus.FAILED) {
            throw new IllegalStateException("Task cannot be started in current status: " + this.status);
        }
        this.status = TaskStatus.RUNNING;
        this.lastExecutionId = executionId;
        this.updatedAt = LocalDateTime.now();
    }

    public void complete() {
        if (this.status != TaskStatus.RUNNING) {
            throw new IllegalStateException("Only running tasks can be completed");
        }
        this.status = TaskStatus.COMPLETED;
        this.updatedAt = LocalDateTime.now();
    }

    public void fail() {
        if (this.status != TaskStatus.RUNNING) {
            throw new IllegalStateException("Only running tasks can be failed");
        }
        this.status = TaskStatus.FAILED;
        this.updatedAt = LocalDateTime.now();
    }

    public void stop() {
        if (this.status != TaskStatus.RUNNING) {
            throw new IllegalStateException("Only running tasks can be stopped");
        }
        this.status = TaskStatus.STOPPED;
        this.updatedAt = LocalDateTime.now();
    }

    public boolean canExecute() {
        return this.status == TaskStatus.READY || this.status == TaskStatus.COMPLETED
               || this.status == TaskStatus.FAILED;
    }

    // Getters
    @Override
    public CollectionTaskId getId() {
        return collectionTaskId;
    }

    public String getName() {
        return name;
    }

    public String getDescription() {
        return description;
    }

    public DataSourceId getSourceDataSourceId() {
        return sourceDataSourceId;
    }

    public DataSourceId getTargetDataSourceId() {
        return targetDataSourceId;
    }

    public Map<String, String> getConfig() {
        return config;
    }

    public TaskStatus getStatus() {
        return status;
    }

    public String getScheduleExpression() {
        return scheduleExpression;
    }

    public String getLastExecutionId() {
        return lastExecutionId;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }
}
