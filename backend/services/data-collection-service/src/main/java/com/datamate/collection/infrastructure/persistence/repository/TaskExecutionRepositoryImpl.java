package com.datamate.collection.infrastructure.persistence.repository;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.datamate.collection.domain.model.entity.TaskExecution;
import com.datamate.collection.domain.repository.TaskExecutionRepository;
import com.datamate.collection.infrastructure.persistence.mapper.TaskExecutionMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;

/**
 * TaskExecutionRepositoryImpl
 *
 * @since 2025/10/23
 */
@Repository
@RequiredArgsConstructor
public class TaskExecutionRepositoryImpl extends ServiceImpl<TaskExecutionMapper, TaskExecution>
    implements TaskExecutionRepository {

    private final TaskExecutionMapper taskExecutionMapper;

    @Override
    public TaskExecution selectLatestByTaskId(String taskId) {
        return taskExecutionMapper.selectLatestByTaskId(taskId);
    }

    @Override
    public void completeExecution(String executionId, String status, LocalDateTime completedAt,
                                  Integer recordsProcessed, Long recordsTotal,
                                  Long recordsSuccess, Long recordsFailed, String errorMessage) {
        taskExecutionMapper.completeExecution(executionId, status, completedAt,
            recordsProcessed, recordsTotal,
            recordsSuccess, recordsFailed, errorMessage);
    }
}
