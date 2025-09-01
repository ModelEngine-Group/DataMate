package com.dataengine.collection.infrastructure.persistence.mapper;

import com.dataengine.collection.domain.model.TaskExecutionLog;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Mapper
public interface TaskExecutionLogMapper {
    int insert(TaskExecutionLog entity);
    int batchInsert(@Param("list") List<TaskExecutionLog> list);
    int deleteById(@Param("id") String id);
    int deleteByExecutionId(@Param("executionId") String executionId);
    TaskExecutionLog selectById(@Param("id") String id);
    List<TaskExecutionLog> selectByExecutionId(@Param("executionId") String executionId, @Param("limit") Integer limit);
    List<TaskExecutionLog> selectByLogLevel(@Param("logLevel") String logLevel, @Param("limit") Integer limit);
    List<TaskExecutionLog> selectAll(Map<String, Object> params);
    long count(Map<String, Object> params);
    int deleteOldLogs(@Param("beforeTime") LocalDateTime beforeTime);
    List<TaskExecutionLog> selectErrorLogs(@Param("executionId") String executionId, @Param("limit") Integer limit);
}
