package com.datamate.cleaning.interfaces.rest;

import com.datamate.cleaning.application.CleaningTaskService;
import com.datamate.cleaning.interfaces.dto.CleaningTaskDto;
import com.datamate.cleaning.interfaces.dto.CreateCleaningTaskRequest;
import com.datamate.common.infrastructure.common.Response;
import com.datamate.common.interfaces.PagedResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;


@RestController
@RequestMapping("/cleaning/tasks")
@RequiredArgsConstructor
public class CleaningTaskController {
    private final CleaningTaskService cleaningTaskService;

    @GetMapping
    public ResponseEntity<Response<PagedResponse<CleaningTaskDto>>> cleaningTasksGet(
            @RequestParam("page") Integer page,
            @RequestParam("size") Integer size, @RequestParam(value = "status", required = false) String status,
            @RequestParam(value = "keywords", required = false) String keywords) {
        List<CleaningTaskDto> tasks = cleaningTaskService.getTasks(status, keywords, page, size);
        int count = cleaningTaskService.countTasks(status, keywords);
        int totalPages = (count + size + 1) / size;
        return ResponseEntity.ok(Response.ok(PagedResponse.of(tasks, page, count, totalPages)));
    }

    @PostMapping
    public ResponseEntity<Response<CleaningTaskDto>> cleaningTasksPost(@RequestBody CreateCleaningTaskRequest request) {
        return ResponseEntity.ok(Response.ok(cleaningTaskService.createTask(request)));
    }

    @PostMapping("/{taskId}/stop")
    public ResponseEntity<Response<Object>> cleaningTasksStop(@PathVariable("taskId") String taskId) {
        cleaningTaskService.stopTask(taskId);
        return ResponseEntity.ok(Response.ok(null));
    }

    @PostMapping("/{taskId}/execute")
    public ResponseEntity<Response<Object>> cleaningTasksStart(@PathVariable("taskId") String taskId) {
        cleaningTaskService.executeTask(taskId);
        return ResponseEntity.ok(Response.ok(null));
    }

    @GetMapping("/{taskId}")
    public ResponseEntity<Response<CleaningTaskDto>> cleaningTasksTaskIdGet(@PathVariable("taskId") String taskId) {
        return ResponseEntity.ok(Response.ok(cleaningTaskService.getTask(taskId)));
    }

    @DeleteMapping("/{taskId}")
    public ResponseEntity<Response<Object>> cleaningTasksTaskIdDelete(@PathVariable("taskId") String taskId) {
        cleaningTaskService.deleteTask(taskId);
        return ResponseEntity.ok(Response.ok(null));
    }
}
