package com.dataengine.collection.infrastructure.persistence;

import com.dataengine.collection.domain.model.CollectionTask;
import com.dataengine.collection.domain.model.TaskStatus;
import com.dataengine.collection.domain.repository.CollectionTaskRepository;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 归集任务JPA仓储实现
 */
@Repository
public interface CollectionTaskJpaRepository extends JpaRepository<CollectionTask, String>, CollectionTaskRepository {

    /**
     * 根据状态查找任务
     */
    @Query("SELECT ct FROM CollectionTask ct WHERE ct.status = :status")
    List<CollectionTask> findByStatus(@Param("status") TaskStatus status);

    /**
     * 根据源数据源ID查找任务
     */
    @Query("SELECT ct FROM CollectionTask ct WHERE ct.sourceDataSourceId = :sourceDataSourceId")
    List<CollectionTask> findBySourceDataSourceId(@Param("sourceDataSourceId") String sourceDataSourceId);

    /**
     * 根据目标数据源ID查找任务
     */
    @Query("SELECT ct FROM CollectionTask ct WHERE ct.targetDataSourceId = :targetDataSourceId")
    List<CollectionTask> findByTargetDataSourceId(@Param("targetDataSourceId") String targetDataSourceId);

    /**
     * 查找所有运行中的任务
     */
    @Query("SELECT ct FROM CollectionTask ct WHERE ct.status = 'RUNNING'")
    List<CollectionTask> findRunningTasks();

    /**
     * 查找可执行的任务
     */
    @Query("SELECT ct FROM CollectionTask ct WHERE ct.status = 'READY'")
    List<CollectionTask> findExecutableTasks();

    /**
     * 根据状态和源数据源ID查找任务
     */
    @Query("SELECT ct FROM CollectionTask ct WHERE (:status IS NULL OR ct.status = :status) AND (:sourceDataSourceId IS NULL OR ct.sourceDataSourceId = :sourceDataSourceId)")
    List<CollectionTask> findByStatusAndSourceDataSourceId(@Param("status") TaskStatus status, @Param("sourceDataSourceId") String sourceDataSourceId);

    /**
     * 查找已配置调度的任务
     */
    @Query("SELECT ct FROM CollectionTask ct WHERE ct.scheduleExpression IS NOT NULL AND ct.scheduleExpression != ''")
    List<CollectionTask> findScheduledTasks();

}
