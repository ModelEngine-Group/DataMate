package com.datamate.cleaning.interfaces.rest;

import com.datamate.cleaning.application.CleaningTaskService;
import com.datamate.cleaning.interfaces.dto.*;
import com.datamate.common.interfaces.PagedResponse;
import lombok.RequiredArgsConstructor;
import org.apache.commons.lang3.StringUtils;
import org.springaicommunity.mcp.annotation.McpTool;
import org.springaicommunity.mcp.annotation.McpToolParam;
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
            @RequestParam(value = "keyword", required = false) String keyword) {
        List<CleaningTaskDto> tasks = cleaningTaskService.getTasks(status, keyword, page, size);
        int count = cleaningTaskService.countTasks(status, keyword);
        int totalPages = (count + size + 1) / size;
        return PagedResponse.of(tasks, page, count, totalPages);
    }

    @PostMapping
    @McpTool(name = "create_cleaning_task", description = "根据模板ID或算子列表创建清洗任务。")
    public CleaningTaskDto cleaningTasksPost(@McpToolParam(description = "创建任务请求体，需要将参数包装在request对象中。")
                                             @RequestBody CreateCleaningTaskRequest request) {
        if (request.getInstance().isEmpty() && StringUtils.isNotBlank(request.getTemplateId())) {
            request.setInstance(cleaningTaskService.getInstanceByTemplateId(request.getTemplateId()));
        }
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

    @DeleteMapping
    public void cleaningTasksDelete(@RequestParam List<String> taskIds) {
        for (String taskId : taskIds) {
            cleaningTaskService.deleteTask(taskId);
        }
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
