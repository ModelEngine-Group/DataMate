package com.dataengine.collection.interfaces.facade;

import com.dataengine.collection.application.service.CollectionTaskService;
import com.dataengine.collection.domain.model.CollectionTask;
import com.dataengine.collection.domain.model.DataxTemplate;
import com.dataengine.collection.interfaces.api.CollectionTaskApi;
import com.dataengine.collection.interfaces.dto.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequiredArgsConstructor
@Validated
public class CollectionTaskController implements CollectionTaskApi {

    private final CollectionTaskService taskService;

    private final ObjectMapper objectMapper = new ObjectMapper();

    private CollectionTaskResponse toResponse(CollectionTask t) {
        CollectionTaskResponse r = new CollectionTaskResponse();
        r.setId(t.getId());
        r.setName(t.getName());
        r.setDescription(t.getDescription());
        r.setStatus(TaskStatus.fromValue(t.getStatus().name()));
        if (t.getSyncMode() != null) { r.setSyncMode(SyncMode.fromValue(t.getSyncMode())); }
        r.setScheduleExpression(t.getScheduleExpression());
        r.setLastExecutionId(t.getLastExecutionId());
        r.setConfig(parseJsonToMap(t.getConfig()));
        r.setCreatedAt(t.getCreatedAt());
        r.setUpdatedAt(t.getUpdatedAt());
        return r;
    }

    private CollectionTaskSummary toSummary(CollectionTask t) {
        CollectionTaskSummary r = new CollectionTaskSummary();
        r.setId(t.getId());
        r.setName(t.getName());
        r.setDescription(t.getDescription());
        r.setStatus(TaskStatus.fromValue(t.getStatus().name()));
        if (t.getSyncMode() != null) { r.setSyncMode(SyncMode.fromValue(t.getSyncMode())); }
        r.setLastExecutionId(t.getLastExecutionId());
        r.setCreatedAt(t.getCreatedAt());
        r.setUpdatedAt(t.getUpdatedAt());
        return r;
    }

    private DataxTemplateSummary toTemplateSummary(DataxTemplate template) {
        DataxTemplateSummary summary = new DataxTemplateSummary();
        summary.setId(template.getId());
        summary.setName(template.getName());
        summary.setSourceType(template.getSourceType());
        summary.setTargetType(template.getTargetType());
        summary.setDescription(template.getDescription());
        summary.setVersion(template.getVersion());
        summary.setIsSystem(template.getIsSystem());
        summary.setCreatedAt(template.getCreatedAt());
        return summary;
    }

    private Map<String, Object> parseJsonToMap(String json) {
        try {
            return objectMapper.readValue(json, Map.class);
        } catch (Exception e) {
            return Map.of();
        }
    }

    private String mapToJsonString(Map<String, Object> map) {
        try {
            return objectMapper.writeValueAsString(map != null ? map : Map.of());
        } catch (Exception e) {
            return "{}";
        }
    }

    @Override
    public ResponseEntity<CollectionTaskResponse> createTask(CreateCollectionTaskRequest body) {
        CollectionTask t = new CollectionTask();
        t.setName(body.getName());
        t.setDescription(body.getDescription());
        t.setConfig(mapToJsonString(body.getConfig()));
        if (body.getSyncMode() != null) { t.setSyncMode(body.getSyncMode().getValue()); }
        t.setScheduleExpression(body.getScheduleExpression());
        t = taskService.create(t);
        return ResponseEntity.status(201).body(toResponse(t));
    }

    @Override
    public ResponseEntity<CollectionTaskResponse> updateTask(String id, UpdateCollectionTaskRequest body) {
        CollectionTask t = taskService.get(id);
        if (t == null) {
            return ResponseEntity.notFound().build();
        }
        t.setId(id);
        t.setName(body.getName());
        t.setDescription(body.getDescription());
        t.setConfig(mapToJsonString(body.getConfig()));
        if (body.getSyncMode() != null) { t.setSyncMode(body.getSyncMode().getValue()); }
        t.setScheduleExpression(body.getScheduleExpression());
        t = taskService.update(t);
        return ResponseEntity.ok(toResponse(t));
    }

    @Override
    public ResponseEntity<Void> deleteTask(String id) {
        taskService.delete(id);
        return ResponseEntity.noContent().build();
    }

    @Override
    public ResponseEntity<CollectionTaskResponse> getTaskDetail(String id) {
        CollectionTask t = taskService.get(id);
        return t == null ? ResponseEntity.notFound().build() : ResponseEntity.ok(toResponse(t));
    }

    @Override
    public ResponseEntity<PagedCollectionTaskSummary> getTasks(Integer page, Integer size, TaskStatus status, String name) {
        var list = taskService.list(page, size, status == null ? null : status.getValue(), name);
        PagedCollectionTaskSummary p = new PagedCollectionTaskSummary();
        p.setContent(list.stream().map(this::toSummary).collect(Collectors.toList()));
        p.setNumber(page);
        p.setSize(size);
        p.setTotalElements(list.size()); // 简化处理，实际项目中应该有单独的count查询
        p.setTotalPages(size == null || size == 0 ? 1 : (int) Math.ceil(list.size() * 1.0 / size));
        return ResponseEntity.ok(p);
    }

    @Override
    public ResponseEntity<PagedDataxTemplates> templatesGet(String sourceType, String targetType,
                                                           Integer page, Integer size) {
        int pageNum = page != null ? page : 0;
        int pageSize = size != null ? size : 20;
        List<DataxTemplate> templates = taskService.listTemplates(sourceType, targetType, pageNum, pageSize);
        int totalElements = taskService.countTemplates(sourceType, targetType);
        PagedDataxTemplates response = new PagedDataxTemplates();
        response.setContent(templates.stream().map(this::toTemplateSummary).collect(Collectors.toList()));
        response.setNumber(pageNum);
        response.setSize(pageSize);
        response.setTotalElements(totalElements);
        response.setTotalPages(pageSize > 0 ? (int) Math.ceil(totalElements * 1.0 / pageSize) : 1);
        return ResponseEntity.ok(response);
    }

}
