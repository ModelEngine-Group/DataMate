package com.datamate.collection.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.collection.domain.model.entity.CollectionTask;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface CollectionTaskMapper extends BaseMapper<CollectionTask> {
    int updateStatus(@Param("id") String id, @Param("status") String status);
    int updateLastExecution(@Param("id") String id, @Param("lastExecutionId") String lastExecutionId);
    List<CollectionTask> selectActiveTasks();
}
