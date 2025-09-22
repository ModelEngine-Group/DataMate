package com.dataengine.operator.domain.repository;

import com.dataengine.operator.domain.modal.CategoryRelation;
import com.dataengine.operator.domain.modal.RelationCategoryDTO;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface CategoryRelationRepository extends JpaRepository<CategoryRelation, Integer> {
    @Query("SELECT new com.dataengine.operator.domain.modal.RelationCategoryDTO(" +
        "tc.id, tcr.operatorId, tc.name, tc.parentId) " +
        "FROM CategoryRelation tcr " +
        "LEFT JOIN tcr.category tc")
    List<RelationCategoryDTO> findAllRelationWithCategory();
}




