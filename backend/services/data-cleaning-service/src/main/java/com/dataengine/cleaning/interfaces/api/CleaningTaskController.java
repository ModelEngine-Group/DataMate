package com.dataengine.cleaning.interfaces.api;

import com.dataengine.cleaning.interfaces.dto.CleaningTask;
import com.dataengine.cleaning.interfaces.dto.CreateCleaningTaskRequest;
import com.dataengine.cleaning.application.service.CleaningTaskService;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
public class CleaningTaskController implements CleaningTaskApi {

    @Autowired
    private CleaningTaskService cleaningTaskService;

    @Override
    public ResponseEntity<List<CleaningTask>> cleaningTasksGet(Integer page, Integer size, String status,
                                                               String keywords) {
        return ResponseEntity.ok(cleaningTaskService.getTasks(status, keywords, page, size));
    }

    @Override
    public ResponseEntity<CleaningTask> cleaningTasksPost(CreateCleaningTaskRequest request) {
        return ResponseEntity.ok(cleaningTaskService.createTask(request));
    }

    @Override
    public ResponseEntity<CleaningTask> cleaningTasksTaskIdGet(String taskId) {
        return ResponseEntity.ok(cleaningTaskService.getTask(taskId));
    }

    @Override
    public ResponseEntity<Void> cleaningTasksTaskIdDelete(String taskId) {
        cleaningTaskService.deleteTask(taskId);
        return ResponseEntity.noContent().build();
    }
}
