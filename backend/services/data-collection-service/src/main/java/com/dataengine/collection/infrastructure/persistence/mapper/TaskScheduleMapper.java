package com.dataengine.collection.infrastructure.persistence.mapper;

import com.dataengine.collection.domain.model.TaskSchedule;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Mapper
public interface TaskScheduleMapper {
    int insert(TaskSchedule entity);
    int update(TaskSchedule entity);
    int deleteById(@Param("id") String id);
    int deleteByTaskId(@Param("taskId") String taskId);
    TaskSchedule selectById(@Param("id") String id);
    TaskSchedule selectByTaskId(@Param("taskId") String taskId);
    List<TaskSchedule> selectEnabledSchedules();
    List<TaskSchedule> selectDueSchedules(@Param("currentTime") LocalDateTime currentTime);
    List<TaskSchedule> selectAll(Map<String, Object> params);
    long count(Map<String, Object> params);
    int updateNextExecutionTime(@Param("id") String id, @Param("nextExecutionTime") LocalDateTime nextExecutionTime);
    int updateLastExecution(@Param("id") String id, @Param("lastExecutionTime") LocalDateTime lastExecutionTime);
    int updateEnabled(@Param("id") String id, @Param("enabled") Boolean enabled);
}
