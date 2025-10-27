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

    private final ExecutorService taskExecutor = Executors.newFixedThreadPool(5);

    public void executeTask(String taskId) {
        taskExecutor.submit(() -> submitTask(taskId));
    }

    private void submitTask(String taskId) {
        CleaningTaskDto task = new CleaningTaskDto();
        task.setId(taskId);
        task.setStatus(CleaningTaskStatusEnum.RUNNING);
        task.setStartedAt(LocalDateTime.now());
        cleaningTaskRepo.updateTask(task);
        RuntimeClient.submitTask(taskId);
    }

    public void stopTask(String taskId) {
        RuntimeClient.stopTask(taskId);
        CleaningTaskDto task = new CleaningTaskDto();
        task.setId(taskId);
        task.setStatus(CleaningTaskStatusEnum.STOPPED);
        cleaningTaskRepo.updateTask(task);
    }
}
