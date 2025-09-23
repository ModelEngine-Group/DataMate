package com.dataengine.collection.infrastructure.persistence.mapper;

import com.dataengine.collection.domain.model.CollectionTask;
import com.dataengine.collection.domain.model.DataxTemplate;
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
    List<CollectionTask> selectAll(Map<String, Object> params);
    int updateStatus(@Param("id") String id, @Param("status") String status);
    int updateLastExecution(@Param("id") String id, @Param("lastExecutionId") String lastExecutionId);
    List<CollectionTask> selectActiveTasks();

    /**
     * 查询模板列表
     *
     * @param sourceType 源数据源类型（可选）
     * @param targetType 目标数据源类型（可选）
     * @param offset 偏移量
     * @param limit 限制数量
     * @return 模板列表
     */
    List<DataxTemplate> selectList(@Param("sourceType") String sourceType,
                                   @Param("targetType") String targetType,
                                   @Param("offset") int offset,
                                   @Param("limit") int limit);

    /**
     * 统计模板数量
     *
     * @param sourceType 源数据源类型（可选）
     * @param targetType 目标数据源类型（可选）
     * @return 模板总数
     */
    int countTemplates(@Param("sourceType") String sourceType,
                       @Param("targetType") String targetType);
}
