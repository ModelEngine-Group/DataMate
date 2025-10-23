package com.datamate.collection.domain.repository;

import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.collection.domain.model.entity.CollectionTask;

import java.util.List;

/**
 * 归集任务仓储层
 *
 * @since 2025/10/23
 */
public interface CollectionTaskRepository extends IRepository<CollectionTask> {
    List<CollectionTask> selectActiveTasks();

    void updateStatus(String id, String status);

    void updateLastExecution(String id, String lastExecutionId);
}
