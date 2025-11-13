package com.datamate.cleaning.interfaces.rest;

import com.datamate.cleaning.application.CleaningTaskService;
import com.datamate.cleaning.interfaces.dto.CleaningResultDto;
import com.datamate.cleaning.interfaces.dto.CleaningTaskDto;
import com.datamate.cleaning.interfaces.dto.CleaningTaskLog;
import com.datamate.cleaning.interfaces.dto.CreateCleaningTaskRequest;
import com.datamate.common.interfaces.PagedResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;


@RestController
@RequestMapping("/cleaning/tasks")
@RequiredArgsConstructor
public class CleaningTaskController {
    private final CleaningTaskService cleaningTaskService;

    @GetMapping
    public PagedResponse<CleaningTaskDto> cleaningTasksGet(
            @RequestParam("page") Integer page,
            @RequestParam("size") Integer size, @RequestParam(value = "status", required = false) String status,
            @RequestParam(value = "keywords", required = false) String keywords) {
        List<CleaningTaskDto> tasks = cleaningTaskService.getTasks(status, keywords, page, size);
        int count = cleaningTaskService.countTasks(status, keywords);
        int totalPages = (count + size + 1) / size;
        return PagedResponse.of(tasks, page, count, totalPages);
    }

    @PostMapping
    public CleaningTaskDto cleaningTasksPost(@RequestBody CreateCleaningTaskRequest request) {
        return cleaningTaskService.createTask(request);
    }

    @PostMapping("/{taskId}/stop")
    public String cleaningTasksStop(@PathVariable("taskId") String taskId) {
        cleaningTaskService.stopTask(taskId);
        return taskId;
    }

    @PostMapping("/{taskId}/execute")
    public String cleaningTasksStart(@PathVariable("taskId") String taskId) {
        cleaningTaskService.executeTask(taskId);
        return taskId;
    }

    @GetMapping("/{taskId}")
    public CleaningTaskDto cleaningTasksTaskIdGet(@PathVariable("taskId") String taskId) {
        return cleaningTaskService.getTask(taskId);
    }

    @DeleteMapping("/{taskId}")
    public String cleaningTasksTaskIdDelete(@PathVariable("taskId") String taskId) {
        cleaningTaskService.deleteTask(taskId);
        return taskId;
    }

    @GetMapping("/{taskId}/result")
    public List<CleaningResultDto> cleaningTasksTaskIdGetResult(@PathVariable("taskId") String taskId) {
        return cleaningTaskService.getTaskResults(taskId);
    }

    @GetMapping("/{taskId}/log")
    public List<CleaningTaskLog> cleaningTasksTaskIdGetLog(@PathVariable("taskId") String taskId) {
        return cleaningTaskService.getTaskLog(taskId);
    }
}
