package com.datamate.cleaning.application.scheduler;

import com.datamate.cleaning.infrastructure.httpclient.RuntimeClient;
import com.datamate.cleaning.common.enums.CleaningTaskStatusEnum;
import com.datamate.cleaning.domain.repository.CleaningTaskRepository;
import com.datamate.cleaning.interfaces.dto.CleaningTaskDto;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Service
@RequiredArgsConstructor
public class CleaningTaskScheduler {
    private final CleaningTaskRepository cleaningTaskRepo;

    private final RuntimeClient runtimeClient;

    private final ExecutorService taskExecutor = Executors.newFixedThreadPool(5);

    public void executeTask(String taskId, int retryCount) {
        taskExecutor.submit(() -> submitTask(taskId, retryCount));
    }

    private void submitTask(String taskId, int retryCount) {
        CleaningTaskDto task = new CleaningTaskDto();
        task.setId(taskId);
        task.setStatus(CleaningTaskStatusEnum.RUNNING);
        task.setStartedAt(LocalDateTime.now());
        task.setRetryCount(retryCount);
        cleaningTaskRepo.updateTask(task);
        runtimeClient.submitTask(taskId);
    }

    public void stopTask(String taskId) {
        runtimeClient.stopTask(taskId);
        CleaningTaskDto task = new CleaningTaskDto();
        task.setId(taskId);
        task.setStatus(CleaningTaskStatusEnum.STOPPED);
        cleaningTaskRepo.updateTask(task);
    }
}
