package com.datamate.collection.domain.model.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import com.datamate.collection.common.enums.TaskStatus;
import com.datamate.common.domain.model.base.BaseEntity;
import lombok.Data;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.UUID;

@Getter
@Setter
@TableName(value = "t_dc_task_executions", autoResultMap = true)
public class TaskExecution extends BaseEntity<String> {
    private String taskId;
    private String taskName;
    private TaskStatus status;
    private Double progress;
    private Long recordsTotal;
    private Long recordsProcessed;
    private Long recordsSuccess;
    private Long recordsFailed;
    private Double throughput;
    private Long dataSizeBytes;
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
    private Integer durationSeconds;
    private String errorMessage;
    private String dataxJobId;
    private String config;
    private String result;

    public static TaskExecution initTaskExecution() {
        TaskExecution exec = new TaskExecution();
        exec.setId(UUID.randomUUID().toString());
        exec.setStatus(TaskStatus.RUNNING);
        exec.setProgress(0.0);
        exec.setStartedAt(LocalDateTime.now());
        exec.setCreatedAt(LocalDateTime.now());
        return exec;
    }
}
