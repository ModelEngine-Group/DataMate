package com.datamate.collection.application;

import com.datamate.collection.common.enums.TemplateType;
import com.datamate.collection.domain.model.entity.CollectionTask;
import com.datamate.collection.domain.model.entity.TaskExecution;
import com.datamate.collection.common.enums.TaskStatus;
import com.datamate.collection.domain.process.ProcessRunner;
import com.datamate.collection.domain.repository.CollectionTaskRepository;
import com.datamate.collection.domain.repository.TaskExecutionRepository;
import com.datamate.datamanagement.application.DatasetApplicationService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

@Slf4j
@Service
@RequiredArgsConstructor
public class TaskExecutionService {
    private final ProcessRunner processRunner;
    private final TaskExecutionRepository executionRepository;
    private final CollectionTaskRepository collectionTaskRepository;
    private final DatasetApplicationService datasetApplicationService;


    @Transactional
    public TaskExecution createExecution(CollectionTask task) {
        TaskExecution exec = TaskExecution.initTaskExecution();
        exec.setTaskId(task.getId());
        exec.setTaskName(task.getName());
        executionRepository.save(exec);
        collectionTaskRepository.updateLastExecution(task.getId(), exec.getId());
        collectionTaskRepository.updateStatus(task.getId(), TaskStatus.RUNNING.name());
        return exec;
    }

    public TaskExecution selectLatestByTaskId(String taskId) {
        return executionRepository.selectLatestByTaskId(taskId);
    }

    @Async
    @Transactional
    public void runAsync(CollectionTask task, String executionId, int timeoutSeconds, String datasetId) {
        try {
            int code = processRunner.runJob(task, executionId, timeoutSeconds);
            log.info("DataX finished with code {} for execution {}", code, executionId);
            // 简化：成功即完成
            executionRepository.completeExecution(executionId, TaskStatus.SUCCESS.name(), LocalDateTime.now(),
                0, 0L, 0L, 0L, null);
            collectionTaskRepository.updateStatus(task.getId(), TaskStatus.SUCCESS.name());
            if (StringUtils.isNotBlank(datasetId)) {
                datasetApplicationService.processDataSourceAsync(datasetId, task.getId());
            }
        } catch (Exception e) {
            log.error("DataX execution failed", e);
            executionRepository.completeExecution(executionId, TaskStatus.FAILED.name(), LocalDateTime.now(),
                0, 0L, 0L, 0L, e.getMessage());
            collectionTaskRepository.updateStatus(task.getId(), TaskStatus.FAILED.name());
        }
    }
}
