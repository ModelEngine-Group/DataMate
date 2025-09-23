package com.dataengine.operator.infrastructure.persistence.mapper;

import com.dataengine.operator.domain.modal.RelationCategoryDTO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface CategoryRelationMapper {

    List<RelationCategoryDTO> findAllRelationWithCategory();

    List<RelationCategoryDTO> findFullOuterJoinNative();
}
