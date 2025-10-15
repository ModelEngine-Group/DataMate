package com.dataengine.cleaning.interfaces.api;

import com.dataengine.cleaning.interfaces.dto.CleaningTask;
import com.dataengine.cleaning.interfaces.dto.CreateCleaningTaskRequest;
import com.dataengine.cleaning.application.service.CleaningTaskService;

import com.dataengine.common.interfaces.PagedResponse;
import com.dataengine.common.interfaces.Response;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/cleaning/tasks")
@RequiredArgsConstructor
public class CleaningTaskController {
    private final CleaningTaskService cleaningTaskService;

    @GetMapping
    public ResponseEntity<Response<PagedResponse<CleaningTask>>> cleaningTasksGet(
            @RequestParam("page") Integer page,
            @RequestParam("size") Integer size, @RequestParam(value = "status", required = false) String status,
            @RequestParam(value = "keywords", required = false) String keywords) {
        return ResponseEntity.ok(Response.ok(PagedResponse.of(cleaningTaskService.getTasks(status, keywords, page,
                size))));
    }

    @PostMapping
    public ResponseEntity<Response<CleaningTask>> cleaningTasksPost(@RequestBody CreateCleaningTaskRequest request) {
        return ResponseEntity.ok(Response.ok(cleaningTaskService.createTask(request)));
    }

    @GetMapping("/{taskId}")
    public ResponseEntity<Response<CleaningTask>> cleaningTasksTaskIdGet(@PathVariable("taskId") String taskId) {
        return ResponseEntity.ok(Response.ok(cleaningTaskService.getTask(taskId)));
    }

    @DeleteMapping("/{taskId}")
    public ResponseEntity<Response<Object>> cleaningTasksTaskIdDelete(@PathVariable("taskId") String taskId) {
        cleaningTaskService.deleteTask(taskId);
        return ResponseEntity.ok(Response.ok(null));
    }
}
