package com.dataengine.collection.application.service;

import com.dataengine.collection.domain.model.CollectionTask;
import com.dataengine.collection.domain.model.TaskExecution;
import com.dataengine.collection.domain.model.TaskStatus;
import com.dataengine.collection.domain.model.TaskStatus;
import com.dataengine.collection.infrastructure.persistence.mapper.CollectionTaskMapper;
import com.dataengine.collection.infrastructure.persistence.mapper.TaskExecutionMapper;
import com.dataengine.collection.infrastructure.runtime.datax.DataxJobBuilder;
import com.dataengine.collection.infrastructure.runtime.datax.DataxProcessRunner;
import com.dataengine.collection.infrastructure.runtime.datax.DataxProperties;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.File;
import java.nio.file.Path;
import java.time.Duration;
import java.time.LocalDateTime;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class DataxExecutionService {

    private final DataxJobBuilder jobBuilder;
    private final DataxProcessRunner processRunner;
    private final DataxProperties props;
    private final TaskExecutionMapper executionMapper;
    private final CollectionTaskMapper taskMapper;


    @Transactional
    public TaskExecution createExecution(CollectionTask task) {

        TaskExecution exec = new TaskExecution();
        exec.setId(UUID.randomUUID().toString());
        exec.setTaskId(task.getId());
        exec.setTaskName(task.getName());
        exec.setStatus(TaskStatus.RUNNING);
        exec.setProgress(0.0);
        exec.setStartedAt(LocalDateTime.now());
        exec.setCreatedAt(LocalDateTime.now());
        executionMapper.insert(exec);
        taskMapper.updateLastExecution(task.getId(), exec.getId());
        taskMapper.updateStatus(task.getId(), TaskStatus.RUNNING.name());
        return exec;
    }

    @Async
    public void runAsync(CollectionTask task, String executionId, int timeoutSeconds) {
        try {
            Path job = jobBuilder.buildJobFile(task);

            int code = processRunner.runJob(job.toFile(), executionId, Duration.ofSeconds(timeoutSeconds));
            log.info("DataX finished with code {} for execution {}", code, executionId);
            // 简化：成功即完成
            executionMapper.completeExecution(executionId, TaskStatus.SUCCESS.name(), LocalDateTime.now(),
                    0, 0L, 0L, 0L, null, null);
            taskMapper.updateStatus(task.getId(), TaskStatus.SUCCESS.name());
        } catch (Exception e) {
            log.error("DataX execution failed", e);
            executionMapper.completeExecution(executionId, TaskStatus.FAILED.name(), LocalDateTime.now(),
                    0, 0L, 0L, 0L, e.getMessage(), null);
            taskMapper.updateStatus(task.getId(), TaskStatus.FAILED.name());
        }
    }
}
