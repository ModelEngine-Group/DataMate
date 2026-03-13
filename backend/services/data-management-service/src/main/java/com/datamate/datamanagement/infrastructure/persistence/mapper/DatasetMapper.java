package com.datamate.datamanagement.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.datamanagement.domain.model.dataset.Dataset;
import com.datamate.datamanagement.interfaces.dto.AllDatasetStatisticsResponse;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.session.RowBounds;

import java.util.List;

@Mapper
public interface DatasetMapper extends BaseMapper<Dataset> {
    Dataset findById(@Param("id") String id);

    /**
     * 使用悲观锁查询数据集（FOR UPDATE）
     */
    @Select("SELECT * FROM t_dm_datasets WHERE id = #{id} FOR UPDATE")
    Dataset findByIdWithLock(@Param("id") String id);
    Dataset findByName(@Param("name") String name);
    List<Dataset> findByStatus(@Param("status") String status);
    List<Dataset> findByCreatedBy(@Param("createdBy") String createdBy, RowBounds rowBounds);
    List<Dataset> findByTypeCode(@Param("typeCode") String typeCode, RowBounds rowBounds);
    List<Dataset> findByTagNames(@Param("tagNames") List<String> tagNames, RowBounds rowBounds);
    List<Dataset> findByKeyword(@Param("keyword") String keyword, RowBounds rowBounds);
    List<Dataset> findByCriteria(@Param("typeCode") String typeCode,
                                 @Param("status") String status,
                                 @Param("keyword") String keyword,
                                 @Param("tagNames") List<String> tagNames,
                                 RowBounds rowBounds);
    long countByCriteria(@Param("typeCode") String typeCode,
                         @Param("status") String status,
                         @Param("keyword") String keyword,
                         @Param("tagNames") List<String> tagNames);

    int deleteById(@Param("id") String id);
    AllDatasetStatisticsResponse getAllDatasetStatistics();
}
