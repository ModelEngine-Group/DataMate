package com.datamate.collection.application;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.datamate.collection.domain.model.entity.CollectionTask;
import com.datamate.collection.domain.model.entity.TaskExecution;
import com.datamate.collection.common.enums.TaskStatus;
import com.datamate.collection.domain.repository.CollectionTaskRepository;
import com.datamate.collection.interfaces.dto.CollectionTaskPagingQuery;
import com.datamate.collection.common.enums.SyncMode;
import com.datamate.common.domain.utils.ChunksSaver;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
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
    public CollectionTask create(CollectionTask task) {
        task.setStatus(TaskStatus.READY);
        task.setCreatedAt(LocalDateTime.now());
        task.setUpdatedAt(LocalDateTime.now());
        collectionTaskRepository.save(task);
        executeTaskNow(task);
        return task;
    }

    private void executeTaskNow(CollectionTask task) {
        if (Objects.equals(task.getSyncMode(), SyncMode.ONCE)) {
            TaskExecution exec = taskExecutionService.createExecution(task);
            int timeout = task.getTimeoutSeconds() == null ? 3600 : task.getTimeoutSeconds();
            taskExecutionService.runAsync(task, exec.getId(), timeout);
            log.info("Triggered DataX execution for task {} at {}, execId={}", task.getId(), LocalDateTime.now(), exec.getId());
        }
    }

    @Transactional
    public CollectionTask update(CollectionTask task) {
        task.setUpdatedAt(LocalDateTime.now());
        collectionTaskRepository.updateById(task);
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

    public IPage<CollectionTask> getTasks(CollectionTaskPagingQuery query) {
        LambdaQueryWrapper<CollectionTask> wrapper = new LambdaQueryWrapper<CollectionTask>()
            .eq(query.getStatus() != null, CollectionTask::getStatus, query.getStatus())
            .like(StringUtils.isNotBlank(query.getName()), CollectionTask::getName, query.getName());
        return collectionTaskRepository.page(new Page<>(query.getPage(), query.getSize()), wrapper);
    }

    public List<CollectionTask> selectActiveTasks() {
        return collectionTaskRepository.selectActiveTasks();
    }
}
