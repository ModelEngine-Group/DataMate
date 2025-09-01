package com.dataengine.collection.infrastructure.persistence.mapper;

import com.dataengine.collection.domain.model.CollectionStatistics;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@Mapper
public interface CollectionStatisticsMapper {
    int insert(CollectionStatistics entity);
    int update(CollectionStatistics entity);
    int deleteById(@Param("id") String id);
    CollectionStatistics selectById(@Param("id") String id);
    CollectionStatistics selectByDateAndPeriod(@Param("statDate") LocalDate statDate, @Param("periodType") String periodType);
    List<CollectionStatistics> selectByDateRange(@Param("startDate") LocalDate startDate, @Param("endDate") LocalDate endDate, @Param("periodType") String periodType);
    List<CollectionStatistics> selectRecentStatistics(@Param("periodType") String periodType, @Param("limit") int limit);
    List<CollectionStatistics> selectAll(Map<String, Object> params);
    long count(Map<String, Object> params);
    int batchInsert(@Param("list") List<CollectionStatistics> list);
    int insertOrUpdate(CollectionStatistics entity);
}
