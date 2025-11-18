package com.datamate.collection.application;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.datamate.collection.domain.model.entity.CollectionTask;
import com.datamate.collection.domain.model.entity.TaskExecution;
import com.datamate.collection.domain.repository.CollectionTaskRepository;
import com.datamate.collection.common.enums.SyncMode;
import com.datamate.common.domain.utils.ChunksSaver;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Objects;

@Slf4j
@Service
@RequiredArgsConstructor
public class CollectionTaskService {
    private final TaskExecutionService taskExecutionService;
    private final CollectionTaskRepository collectionTaskRepository;

    @Transactional
    public CollectionTask create(CollectionTask task, String datasetId) {
        task.initCreateParam();
        collectionTaskRepository.save(task);
        executeTaskNow(task, datasetId);
        return task;
    }

    private void executeTaskNow(CollectionTask task, String datasetId) {
        if (Objects.equals(task.getSyncMode(), SyncMode.ONCE)) {
            TaskExecution exec = taskExecutionService.createExecution(task);
            int timeout = task.getTimeoutSeconds() == null ? 3600 : task.getTimeoutSeconds();
            taskExecutionService.runAsync(task, exec.getId(), timeout, datasetId);
            log.info("Triggered DataX execution for task {} at {}, execId={}", task.getId(), LocalDateTime.now(), exec.getId());
        }
    }

    @Transactional
    public CollectionTask update(CollectionTask task, String datasetId) {
        task.setUpdatedAt(LocalDateTime.now());
        task.addPath();
        collectionTaskRepository.updateById(task);
        executeTaskNow(task, datasetId);
        return task;
    }

    @Transactional
    public void delete(String id) {
        CollectionTask task = collectionTaskRepository.getById(id);
        if (task != null) {
            ChunksSaver.deleteFolder("/dataset/local/" + task.getId());
        }
        collectionTaskRepository.removeById(id);
    }

    public CollectionTask get(String id) {
        return collectionTaskRepository.getById(id);
    }

    public IPage<CollectionTask> getTasks(Page<CollectionTask> page, LambdaQueryWrapper<CollectionTask> wrapper) {
        return collectionTaskRepository.page(page, wrapper);
    }

    public List<CollectionTask> selectActiveTasks() {
        return collectionTaskRepository.selectActiveTasks();
    }
}
