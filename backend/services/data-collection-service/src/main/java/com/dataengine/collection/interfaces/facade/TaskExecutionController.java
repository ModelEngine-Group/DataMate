package com.dataengine.collection.interfaces.facade;

import com.dataengine.collection.application.service.CollectionTaskService;
import com.dataengine.collection.application.service.TaskExecutionService;
import com.dataengine.collection.domain.model.TaskExecution;
import com.dataengine.collection.interfaces.api.TaskExecutionApi;
import com.dataengine.collection.interfaces.dto.PagedTaskExecutions;
import com.dataengine.collection.interfaces.dto.TaskExecutionDetail;
import com.dataengine.collection.interfaces.dto.TaskExecutionResponse;
import com.dataengine.collection.interfaces.dto.TaskStatus; // DTO enum
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.stream.Collectors;

@RestController
@RequiredArgsConstructor
@Validated
public class TaskExecutionController implements TaskExecutionApi {

    private final TaskExecutionService executionService;
    private final CollectionTaskService taskService;

    private TaskExecutionDetail toDetail(TaskExecution e) {
        TaskExecutionDetail d = new TaskExecutionDetail();
        d.setId(e.getId());
        d.setTaskId(e.getTaskId());
        d.setTaskName(e.getTaskName());
        if (e.getStatus() != null) { d.setStatus(TaskStatus.fromValue(e.getStatus().name())); }
        d.setProgress(e.getProgress());
        d.setRecordsTotal(e.getRecordsTotal() != null ? e.getRecordsTotal().intValue() : null);
        d.setRecordsProcessed(e.getRecordsProcessed() != null ? e.getRecordsProcessed().intValue() : null);
        d.setRecordsSuccess(e.getRecordsSuccess() != null ? e.getRecordsSuccess().intValue() : null);
        d.setRecordsFailed(e.getRecordsFailed() != null ? e.getRecordsFailed().intValue() : null);
        d.setThroughput(e.getThroughput());
        d.setDataSizeBytes(e.getDataSizeBytes() != null ? e.getDataSizeBytes().intValue() : null);
        d.setStartedAt(e.getStartedAt());
        d.setCompletedAt(e.getCompletedAt());
        d.setDurationSeconds(e.getDurationSeconds());
        d.setErrorMessage(e.getErrorMessage());
        return d;
    }

    // GET /executions/{id}
    @Override
    public ResponseEntity<TaskExecutionDetail> executionsIdGet(String id) {
        var exec = executionService.get(id);
        return exec == null ? ResponseEntity.notFound().build() : ResponseEntity.ok(toDetail(exec));
    }

    // DELETE /executions/{id}
    @Override
    public ResponseEntity<Void> executionsIdDelete(String id) {
        executionService.stop(id); // 幂等处理，在service内部判断状态
        return ResponseEntity.noContent().build();
    }

    // POST /tasks/{id}/execute  -> 201
    @Override
    public ResponseEntity<TaskExecutionResponse> tasksIdExecutePost(String id) {
        var task = taskService.get(id);
        if (task == null) { return ResponseEntity.notFound().build(); }
        var latestExec = executionService.getLatestByTaskId(id);
        if (latestExec != null && latestExec.getStatus() == com.dataengine.collection.domain.model.TaskStatus.RUNNING) {
            TaskExecutionResponse r = new TaskExecutionResponse();
            r.setId(latestExec.getId());
            r.setTaskId(latestExec.getTaskId());
            r.setTaskName(latestExec.getTaskName());
            r.setStatus(TaskStatus.fromValue(latestExec.getStatus().name()));
            r.setStartedAt(latestExec.getStartedAt());
            return ResponseEntity.status(HttpStatus.CREATED).body(r); // 返回已有运行实例
        }
        var exec = taskService.startExecution(task);
        TaskExecutionResponse r = new TaskExecutionResponse();
        r.setId(exec.getId());
        r.setTaskId(exec.getTaskId());
        r.setTaskName(exec.getTaskName());
        r.setStatus(TaskStatus.fromValue(exec.getStatus().name()));
        r.setStartedAt(exec.getStartedAt());
        return ResponseEntity.status(HttpStatus.CREATED).body(r);
    }

    // GET /tasks/{id}/executions  -> 分页
    @Override
    public ResponseEntity<PagedTaskExecutions> tasksIdExecutionsGet(String id, Integer page, Integer size) {
        if (page == null || page < 0) { page = 0; }
        if (size == null || size <= 0) { size = 20; }
        var list = executionService.list(id, null, null, null, page, size);
        long total = executionService.count(id, null, null, null);
        PagedTaskExecutions p = new PagedTaskExecutions();
        p.setContent(list.stream().map(this::toDetail).collect(Collectors.toList()));
        p.setNumber(page);
        p.setSize(size);
        p.setTotalElements((int) total);
        p.setTotalPages(size == 0 ? 1 : (int) Math.ceil(total * 1.0 / size));
        return ResponseEntity.ok(p);
    }
}
