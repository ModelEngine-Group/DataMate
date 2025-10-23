package com.datamate.collection.interfaces.rest;

import com.datamate.collection.application.CollectionTaskService;
import com.datamate.collection.domain.model.entity.CollectionTask;
import com.datamate.collection.interfaces.converter.CollectionTaskConverter;
import com.datamate.collection.interfaces.dto.*;
import com.datamate.common.interfaces.PagedResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@Slf4j
@RestController
@RequestMapping("/data-collection/tasks")
@RequiredArgsConstructor
public class CollectionTaskController{

    private final CollectionTaskService taskService;

    @PostMapping
    public ResponseEntity<CollectionTaskResponse> createTask(@Valid @RequestBody CreateCollectionTaskRequest request) {
        CollectionTask task = CollectionTaskConverter.INSTANCE.toCollectionTask(request);
        task.setId(UUID.randomUUID().toString());
        task.addPath();
        return ResponseEntity.ok().body(CollectionTaskConverter.INSTANCE.toResponse(taskService.create(task)));
    }

    @PutMapping("/{id}")
    public ResponseEntity<CollectionTaskResponse> updateTask(@PathVariable("id") String id, @Valid @RequestBody UpdateCollectionTaskRequest request) {
        if (taskService.get(id) == null) {
            return ResponseEntity.notFound().build();
        }
        CollectionTask task = CollectionTaskConverter.INSTANCE.toCollectionTask(request);
        task.setId(id);
        return ResponseEntity.ok(CollectionTaskConverter.INSTANCE.toResponse(taskService.update(task)));
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
        return ResponseEntity.ok(CollectionTaskConverter.INSTANCE.toResponse(taskService.getTasks(query)));
    }
}
