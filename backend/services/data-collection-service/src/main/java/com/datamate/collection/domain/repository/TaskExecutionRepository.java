package com.datamate.collection.domain.repository;

import com.baomidou.mybatisplus.extension.service.IService;
import com.datamate.collection.domain.model.entity.TaskExecution;

import java.time.LocalDateTime;

/**
 * TaskExecutionRepository
 *
 * @since 2025/10/23
 */
public interface TaskExecutionRepository extends IService<TaskExecution> {
    TaskExecution selectLatestByTaskId(String taskId);

    void completeExecution(String executionId, String status, LocalDateTime completedAt,
                           Integer recordsProcessed, Long recordsTotal,
                           Long recordsSuccess, Long recordsFailed, String errorMessage);
}
