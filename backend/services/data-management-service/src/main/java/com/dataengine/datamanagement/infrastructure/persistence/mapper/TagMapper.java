package com.dataengine.datamanagement.infrastructure.persistence.mapper;

import com.dataengine.datamanagement.domain.model.dataset.Tag;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface TagMapper {
    Tag findById(@Param("id") String id);
    Tag findByName(@Param("name") String name);
    List<Tag> findByNameIn(@Param("list") List<String> names);
    List<Tag> findByIdIn(@Param("ids") List<String> ids);
    List<Tag> findByKeyword(@Param("keyword") String keyword);
    List<Tag> findAllByOrderByUsageCountDesc();

    int insert(Tag tag);
    int update(Tag tag);
    int updateUsageCount(@Param("id") String id, @Param("usageCount") Long usageCount);

    // Relations with dataset
    int insertDatasetTag(@Param("datasetId") String datasetId, @Param("tagId") String tagId);
    int deleteDatasetTagsByDatasetId(@Param("datasetId") String datasetId);
    List<Tag> findByDatasetId(@Param("datasetId") String datasetId);
    void deleteTagsById(@Param("ids") List<String> ids);
}
