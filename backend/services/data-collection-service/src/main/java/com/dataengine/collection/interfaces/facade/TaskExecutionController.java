package com.dataengine.collection.interfaces.facade;

import com.dataengine.collection.application.service.CollectionTaskService;
import com.dataengine.collection.application.service.TaskExecutionService;
import com.dataengine.collection.domain.model.TaskExecution;
import com.dataengine.collection.interfaces.api.TaskExecutionApi;
import com.dataengine.collection.interfaces.dto.PagedTaskExecutions;
import com.dataengine.collection.interfaces.dto.TaskExecutionDetail;
import com.dataengine.collection.interfaces.dto.TaskExecutionResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

import java.time.OffsetDateTime;
import java.util.stream.Collectors;

@RestController
@RequiredArgsConstructor
@Validated
public class TaskExecutionController implements TaskExecutionApi {

    private final TaskExecutionService executionService;
    private final CollectionTaskService taskService;

    private TaskExecutionDetail toDetail(TaskExecution e) {
        TaskExecutionDetail d = new TaskExecutionDetail();
        d.setExecutionId(e.getId());
        d.setTaskId(e.getTaskId());
        d.setTaskName(e.getTaskName());
        // map execution status: RUNNING/SUCCESS/FAILED/STOPPED
        d.setStatus(TaskExecutionDetail.StatusEnum.fromValue(e.getStatus().name()));
        d.setProgress(e.getProgress());
        d.setRecordsProcessed(e.getRecordsProcessed());
        d.setRecordsFailed(e.getRecordsFailed());
        return d;
    }

    @Override
    public ResponseEntity<PagedTaskExecutions> executionsGet(Integer page, Integer size, String taskId, String status, java.time.OffsetDateTime startTime, java.time.OffsetDateTime endTime) {
        var list = executionService.list(taskId, status, null, null, page, size);
        long total = executionService.count(taskId, status, null, null);
        PagedTaskExecutions p = new PagedTaskExecutions();
        p.setContent(list.stream().map(this::toDetail).collect(Collectors.toList()));
        p.setNumber(page);
        p.setSize(size);
        p.setTotalElements(total);
        p.setTotalPages(size == null || size == 0 ? 1 : (int) Math.ceil(total * 1.0 / size));
        p.setFirst(page != null && page == 0);
        p.setLast(page != null && size != null && (page + 1) * size >= total);
        return ResponseEntity.ok(p);
    }

    @Override
    public ResponseEntity<TaskExecutionDetail> executionsExecutionIdGet(String executionId) {
        var e = executionService.list(null, null, null, null, 0, 1).stream().findFirst().orElse(null);
        return e == null ? ResponseEntity.notFound().build() : ResponseEntity.ok(toDetail(e));
    }

    @Override
    public ResponseEntity<TaskExecutionResponse> tasksIdExecutePost(String id) {
        var task = taskService.get(id);
        var exec = taskService.startExecution(task);
        TaskExecutionResponse r = new TaskExecutionResponse();
        r.setExecutionId(exec.getId());
        r.setTaskId(exec.getTaskId());
        r.setStatus(TaskExecutionResponse.StatusEnum.RUNNING);
        r.setStartedAt(OffsetDateTime.now());
        return ResponseEntity.accepted().body(r);
    }

    @Override
    public ResponseEntity<Void> tasksIdStopPost(String id) {
        return ResponseEntity.ok().build();
    }
}
