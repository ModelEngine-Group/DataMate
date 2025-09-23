package com.dataengine.collection.application.service;

import com.dataengine.collection.domain.model.CollectionTask;
import com.dataengine.collection.domain.model.TaskExecution;
import com.dataengine.collection.domain.model.TaskStatus;
import com.dataengine.collection.infrastructure.persistence.mapper.CollectionTaskMapper;
import com.dataengine.collection.infrastructure.persistence.mapper.TaskExecutionMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class TaskExecutionService {
    private final TaskExecutionMapper executionMapper;
    private final CollectionTaskMapper taskMapper;

    public List<TaskExecution> list(String taskId, String status, LocalDateTime startDate,
                                    LocalDateTime endDate, Integer page, Integer size) {
        Map<String, Object> p = new HashMap<>();
        p.put("taskId", taskId);
        p.put("status", status);
        p.put("startDate", startDate);
        p.put("endDate", endDate);
        if (page != null && size != null) {
            p.put("offset", page * size);
            p.put("limit", size);
        }
        return executionMapper.selectAll(p);
    }

    public long count(String taskId, String status, LocalDateTime startDate, LocalDateTime endDate) {
        Map<String, Object> p = new HashMap<>();
        p.put("taskId", taskId);
        p.put("status", status);
        p.put("startDate", startDate);
        p.put("endDate", endDate);
        return executionMapper.count(p);
    }

    // --- Added convenience methods ---
    public TaskExecution get(String id) { return executionMapper.selectById(id); }
    public TaskExecution getLatestByTaskId(String taskId) { return executionMapper.selectLatestByTaskId(taskId); }

    @Transactional
    public void complete(String executionId, boolean success, long successCount, long failedCount,
                         long dataSizeBytes, String errorMessage, String resultJson) {
        LocalDateTime now = LocalDateTime.now();
        TaskExecution exec = executionMapper.selectById(executionId);
        if (exec == null) { return; }
        int duration = (int) Duration.between(exec.getStartedAt(), now).getSeconds();
        executionMapper.completeExecution(executionId, success ? TaskStatus.SUCCESS.name() : TaskStatus.FAILED.name(),
                now, duration, successCount, failedCount, dataSizeBytes, errorMessage, resultJson);
        CollectionTask task = taskMapper.selectById(exec.getTaskId());
        if (task != null) {
            taskMapper.updateStatus(task.getId(), success ? TaskStatus.SUCCESS.name() : TaskStatus.FAILED.name());
        }
    }

    @Transactional
    public void stop(String executionId) {
        TaskExecution exec = executionMapper.selectById(executionId);
        if (exec == null || exec.getStatus() != TaskStatus.RUNNING) { return; }
        LocalDateTime now = LocalDateTime.now();
        int duration = (int) Duration.between(exec.getStartedAt(), now).getSeconds();
        // Reuse completeExecution to persist STOPPED status and timing info
        executionMapper.completeExecution(exec.getId(), TaskStatus.STOPPED.name(), now, duration,
                exec.getRecordsSuccess(), exec.getRecordsFailed(), exec.getDataSizeBytes(), null, exec.getResult());
        taskMapper.updateStatus(exec.getTaskId(), TaskStatus.STOPPED.name());
    }

    @Transactional
    public void stopLatestByTaskId(String taskId) {
        TaskExecution latest = executionMapper.selectLatestByTaskId(taskId);
        if (latest != null) { stop(latest.getId()); }
    }
}
