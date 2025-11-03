package com.datamate.collection.interfaces.rest;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.datamate.collection.application.CollectionTaskService;
import com.datamate.collection.domain.model.entity.CollectionTask;
import com.datamate.collection.interfaces.converter.CollectionTaskConverter;
import com.datamate.collection.interfaces.dto.*;
import com.datamate.common.interfaces.PagedResponse;
import com.datamate.datamanagement.application.DatasetApplicationService;
import com.datamate.datamanagement.domain.model.dataset.Dataset;
import com.datamate.datamanagement.interfaces.converter.DatasetConverter;
import com.datamate.datamanagement.interfaces.dto.DatasetResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@Slf4j
@RestController
@RequestMapping("/data-collection/tasks")
@RequiredArgsConstructor
public class CollectionTaskController{

    private final CollectionTaskService taskService;

    private final DatasetApplicationService datasetService;

    @PostMapping
    @Transactional
    public ResponseEntity<CollectionTaskResponse> createTask(@Valid @RequestBody CreateCollectionTaskRequest request) {
        CollectionTask task = CollectionTaskConverter.INSTANCE.toCollectionTask(request);
        String datasetId = null;
        DatasetResponse dataset = null;
        if (Objects.nonNull(request.getDataset())) {
            dataset = DatasetConverter.INSTANCE.convertToResponse(datasetService.createDataset(request.getDataset()));
            datasetId = dataset.getId();
        }
        CollectionTaskResponse response = CollectionTaskConverter.INSTANCE.toResponse(taskService.create(task, datasetId));
        response.setDataset(dataset);
        return ResponseEntity.ok().body(response);
    }

    @PutMapping("/{id}")
    public ResponseEntity<CollectionTaskResponse> updateTask(@PathVariable("id") String id, @Valid @RequestBody UpdateCollectionTaskRequest request) {
        if (taskService.get(id) == null) {
            return ResponseEntity.notFound().build();
        }
        CollectionTask task = CollectionTaskConverter.INSTANCE.toCollectionTask(request);
        task.setId(id);
        return ResponseEntity.ok(CollectionTaskConverter.INSTANCE.toResponse(taskService.update(task, request.getDatasetId())));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteTask(@PathVariable("id") String id) {
        taskService.delete(id);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/{id}")
    public ResponseEntity<CollectionTaskResponse> getTaskDetail(@PathVariable("id") String id) {
        CollectionTask task = taskService.get(id);
        return task == null ? ResponseEntity.notFound().build() : ResponseEntity.ok(CollectionTaskConverter.INSTANCE.toResponse(task));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<CollectionTaskResponse>> getTasks(@Valid CollectionTaskPagingQuery query) {
        Page<CollectionTask> page = new Page<>(query.getPage(), query.getSize());
        LambdaQueryWrapper<CollectionTask> wrapper = new LambdaQueryWrapper<CollectionTask>()
            .eq(query.getStatus() != null, CollectionTask::getStatus, query.getStatus())
            .like(StringUtils.isNotBlank(query.getName()), CollectionTask::getName, query.getName());
        return ResponseEntity.ok(CollectionTaskConverter.INSTANCE.toResponse(taskService.getTasks(page, wrapper)));
    }
}
