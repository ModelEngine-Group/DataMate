package com.dataengine.collection.interfaces.facade;

import com.dataengine.collection.application.service.CollectionTaskService;
import com.dataengine.collection.application.service.DataxExecutionService;
import com.dataengine.collection.domain.model.CollectionTask;
import com.dataengine.collection.interfaces.api.CollectionTaskApi;
import com.dataengine.collection.interfaces.dto.*;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequiredArgsConstructor
@Validated
public class CollectionTaskController implements CollectionTaskApi {

    private final CollectionTaskService taskService;
    private final DataxExecutionService dataxExecutionService;

    private CollectionTaskResponse toResponse(CollectionTask t) {
        CollectionTaskResponse r = new CollectionTaskResponse();
        r.setId(t.getId());
        r.setName(t.getName());
        r.setDescription(t.getDescription());
        r.setSourceDataSourceId(t.getSourceDataSourceId());
        r.setTargetDataSourceId(t.getTargetDataSourceId());
        r.setStatus(TaskStatus.fromValue(t.getStatus().name()));
        r.setScheduleExpression(t.getScheduleExpression());
        r.setLastExecutionId(t.getLastExecutionId());
        return r;
    }

    @Override
    public ResponseEntity<CollectionTaskResponse> tasksPost(CreateCollectionTaskRequest body) {
        CollectionTask t = new CollectionTask();
        t.setName(body.getName());
        t.setDescription(body.getDescription());
        t.setSourceDataSourceId(body.getSourceDataSourceId());
        t.setTargetDataSourceId(body.getTargetDataSourceId());
        t.setConfig("{}");
        t.setScheduleExpression(body.getScheduleExpression());
        t = taskService.create(t);
        return ResponseEntity.status(201).body(toResponse(t));
    }

    @Override
    public ResponseEntity<CollectionTaskResponse> tasksIdPut(String id, UpdateCollectionTaskRequest body) {
        CollectionTask t = new CollectionTask();
        t.setId(id);
        t.setName(body.getName());
        t.setDescription(body.getDescription());
//        t.setSourceDataSourceId(body.getSourceDataSourceId());
//        t.setTargetDataSourceId(body.getTargetDataSourceId());
        t.setConfig("{}");
        t.setScheduleExpression(body.getScheduleExpression());
        t = taskService.update(t);
        return ResponseEntity.ok(toResponse(t));
    }

    @Override
    public ResponseEntity<Void> tasksIdDelete(String id) {
        taskService.delete(id);
        return ResponseEntity.noContent().build();
    }

    @Override
    public ResponseEntity<CollectionTaskResponse> tasksIdGet(String id) {
        CollectionTask t = taskService.get(id);
        return t == null ? ResponseEntity.notFound().build() : ResponseEntity.ok(toResponse(t));
    }

    @Override
    public ResponseEntity<PagedCollectionTasks> tasksGet(Integer page, Integer size, TaskStatus status, String name) {
        var list = taskService.list(page, size, status == null ? null : status.getValue(), name, null, null);
        long total = taskService.count(status == null ? null : status.getValue(), name, null, null);
        PagedCollectionTasks p = new PagedCollectionTasks();
        p.setContent(list.stream().map(this::toResponse).collect(Collectors.toList()));
        p.setNumber(page);
        p.setSize(size);
        p.setTotalElements(total);
        p.setTotalPages(size == null || size == 0 ? 1 : (int) Math.ceil(total * 1.0 / size));
        p.setFirst(page != null && page == 0);
        p.setLast(page != null && size != null && (page + 1) * size >= total);
        return ResponseEntity.ok(p);
    }

}
