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

    @Query(value = "SELECT toc.id, tocr.operator_id, toc.name, toc.parent_id FROM dataengine" +
            ".t_operator_category_relation tocr " +
        "LEFT JOIN dataengine.t_operator_category toc ON tocr.category_id = toc.id " +
        "UNION " +
        "SELECT toc.id, tocr.operator_id, toc.name, toc.parent_id FROM dataengine.t_operator_category_relation tocr " +
        "RIGHT JOIN dataengine.t_operator_category toc ON tocr.category_id = toc.id",
        nativeQuery = true)
    List<Object[]> findFullOuterJoinNative();
}




