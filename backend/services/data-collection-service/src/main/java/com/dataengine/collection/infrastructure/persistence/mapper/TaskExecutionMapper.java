package com.dataengine.collection.infrastructure.persistence.mapper;

import com.dataengine.collection.domain.model.TaskExecution;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Mapper
public interface TaskExecutionMapper {
    int insert(TaskExecution entity);
    int update(TaskExecution entity);
    int deleteById(@Param("id") String id);
    TaskExecution selectById(@Param("id") String id);
    List<TaskExecution> selectByTaskId(@Param("taskId") String taskId, @Param("limit") Integer limit);
    List<TaskExecution> selectByStatus(@Param("status") String status);
    List<TaskExecution> selectAll(Map<String, Object> params);
    long count(Map<String, Object> params);
    int updateProgress(@Param("id") String id,
                       @Param("status") String status,
                       @Param("progress") Double progress,
                       @Param("recordsProcessed") Long recordsProcessed,
                       @Param("throughput") Double throughput);
    int completeExecution(@Param("id") String id,
                          @Param("status") String status,
                          @Param("completedAt") LocalDateTime completedAt,
                          @Param("durationSeconds") Integer durationSeconds,
                          @Param("recordsSuccess") Long recordsSuccess,
                          @Param("recordsFailed") Long recordsFailed,
                          @Param("dataSizeBytes") Long dataSizeBytes,
                          @Param("errorMessage") String errorMessage,
                          @Param("result") String result);
    List<TaskExecution> selectRunningExecutions();
    TaskExecution selectLatestByTaskId(@Param("taskId") String taskId);
    int deleteOldExecutions(@Param("beforeDate") LocalDateTime beforeDate);
}
