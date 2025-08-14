package com.dataengine.collection.domain.repository;

import com.dataengine.collection.domain.model.CollectionTask;
import com.dataengine.collection.domain.model.CollectionTaskId;
import com.dataengine.collection.domain.model.DataSourceId;
import com.dataengine.collection.domain.model.TaskStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.List;
import java.util.Optional;

/**
 * 数据归集任务仓储接口
 */
public interface CollectionTaskRepository {

    /**
     * 保存归集任务
     */
    CollectionTask save(CollectionTask task);

    /**
     * 根据ID查找归集任务
     */
    Optional<CollectionTask> findById(CollectionTaskId id);

    /**
     * 分页查询归集任务
     */
    Page<CollectionTask> findAll(Pageable pageable);

    /**
     * 根据状态查询归集任务
     */
    Page<CollectionTask> findByStatus(TaskStatus status, Pageable pageable);

    /**
     * 根据数据源查询归集任务
     */
    List<CollectionTask> findBySourceDataSourceId(DataSourceId sourceDataSourceId);

    /**
     * 根据目标数据源查询归集任务
     */
    List<CollectionTask> findByTargetDataSourceId(DataSourceId targetDataSourceId);

    /**
     * 查询可执行的任务
     */
    List<CollectionTask> findExecutableTasks();

    /**
     * 查询运行中的任务
     */
    List<CollectionTask> findRunningTasks();

    /**
     * 删除归集任务
     */
    void delete(CollectionTask task);

    /**
     * 根据ID删除归集任务
     */
    void deleteById(CollectionTaskId id);

    /**
     * 检查归集任务是否存在
     */
    boolean existsById(CollectionTaskId id);
}
