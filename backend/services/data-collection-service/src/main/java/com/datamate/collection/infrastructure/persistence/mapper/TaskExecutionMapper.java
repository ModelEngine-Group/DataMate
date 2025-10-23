package com.datamate.collection.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.collection.domain.model.entity.TaskExecution;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDateTime;

@Mapper
public interface TaskExecutionMapper extends BaseMapper<TaskExecution> {
    TaskExecution selectLatestByTaskId(@Param("taskId") String taskId);

    void completeExecution(@Param("executionId") String executionId,
                           @Param("status") String status,
                           @Param("completedAt") LocalDateTime completedAt,
                           @Param("recordsProcessed") Integer recordsProcessed,
                           @Param("recordsTotal") Long recordsTotal,
                           @Param("recordsSuccess") Long recordsSuccess,
                           @Param("recordsFailed") Long recordsFailed,
                           @Param("errorMessage") String errorMessage);
}
