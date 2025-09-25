package com.dataengine.cleaning.application.service;


import com.dataengine.cleaning.infrastructure.persistence.mapper.CleaningTaskMapper;
import com.dataengine.cleaning.interfaces.dto.CleaningTask;
import com.dataengine.cleaning.interfaces.dto.CreateCleaningTaskRequest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Service
public class CleaningTaskService {

    @Autowired
    private CleaningTaskMapper cleaningTaskMapper;

    private final ExecutorService taskExecutor = Executors.newFixedThreadPool(5);

    public List<CleaningTask> getTasks(String status) {
        return cleaningTaskMapper.findTasksByStatus(status);
    }

    @Transactional
    public CleaningTask createTask(CreateCleaningTaskRequest request) {
        CleaningTask task = new CleaningTask();
        task.setName(request.getName());
        task.setDescription(request.getDescription());
        task.setStatus(CleaningTask.StatusEnum.PENDING);
        task.setId(UUID.randomUUID().toString());
        cleaningTaskMapper.insertTask(task);

        taskExecutor.submit(() -> executeTask(task));
        return task;
    }

    public CleaningTask getTask(String taskId) {
        return cleaningTaskMapper.findTaskById(taskId);
    }

    @Transactional
    public void deleteTask(String taskId) {
        cleaningTaskMapper.deleteTask(taskId);
    }

    private void executeTask(CleaningTask task) {
        task.setStatus(CleaningTask.StatusEnum.RUNNING);
        cleaningTaskMapper.updateTaskStatus(task);
        String raySubmitId = submitTaskToRay(task);
        trackTaskStatus(raySubmitId);
        task.setStatus(CleaningTask.StatusEnum.COMPLETED);
        cleaningTaskMapper.updateTaskStatus(task);
    }

    private String submitTaskToRay(CleaningTask task) {
        return "";
    }

    private void trackTaskStatus (String submitId) {

    }
}
