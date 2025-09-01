package com.dataengine.collection.infrastructure.persistence.mapper;

import com.dataengine.collection.domain.model.CollectionTask;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Map;

@Mapper
public interface CollectionTaskMapper {
    int insert(CollectionTask entity);
    int update(CollectionTask entity);
    int deleteById(@Param("id") String id);
    CollectionTask selectById(@Param("id") String id);
    CollectionTask selectByName(@Param("name") String name);
    List<CollectionTask> selectByStatus(@Param("status") String status);
    List<CollectionTask> selectByDataSource(@Param("dataSourceId") String dataSourceId);
    List<CollectionTask> selectAll(Map<String, Object> params);
    long count(Map<String, Object> params);
    int updateStatus(@Param("id") String id, @Param("status") String status);
    int updateLastExecution(@Param("id") String id, @Param("lastExecutionId") String lastExecutionId);
    List<CollectionTask> selectActiveTasks();
}
