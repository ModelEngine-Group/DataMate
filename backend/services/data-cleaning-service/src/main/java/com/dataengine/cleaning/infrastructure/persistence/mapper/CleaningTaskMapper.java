package com.dataengine.cleaning.infrastructure.persistence.mapper;

import com.dataengine.cleaning.interfaces.dto.CleaningTask;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface CleaningTaskMapper {
    List<CleaningTask> findTasksByStatus(@Param("status") String status, @Param("keywords") String keywords,
                                         @Param("size") Integer size, @Param("offset") Integer offset);

    CleaningTask findTaskById(@Param("taskId") String taskId);

    void insertTask(CleaningTask task);

    void updateTaskStatus(CleaningTask task);

    void deleteTask(@Param("taskId") String taskId);
}
