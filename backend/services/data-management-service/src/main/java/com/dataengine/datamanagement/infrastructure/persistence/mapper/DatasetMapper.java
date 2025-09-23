package com.dataengine.datamanagement.infrastructure.persistence.mapper;

import com.dataengine.datamanagement.domain.model.dataset.Dataset;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.session.RowBounds;

import java.util.List;

@Mapper
public interface DatasetMapper {
    Dataset findById(@Param("id") String id);
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

    int insert(Dataset dataset);
    int update(Dataset dataset);
    int deleteById(@Param("id") String id);
}
