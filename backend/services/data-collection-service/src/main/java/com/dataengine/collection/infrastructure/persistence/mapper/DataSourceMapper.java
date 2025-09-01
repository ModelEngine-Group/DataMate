package com.dataengine.collection.infrastructure.persistence.mapper;

import com.dataengine.collection.domain.model.DataSource;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Map;

@Mapper
public interface DataSourceMapper {
    int insert(DataSource entity);
    int update(DataSource entity);
    int deleteById(@Param("id") String id);
    DataSource selectById(@Param("id") String id);
    DataSource selectByName(@Param("name") String name);
    List<DataSource> selectByType(@Param("type") String type);
    List<DataSource> selectByStatus(@Param("status") String status);
    List<DataSource> selectAll(Map<String, Object> params);
    long count(Map<String, Object> params);
    int updateStatus(@Param("id") String id, @Param("status") String status);
    int updateTestResult(@Param("id") String id, @Param("lastTestAt") java.time.LocalDateTime lastTestAt, @Param("lastTestResult") String lastTestResult);
}
