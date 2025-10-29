package com.datamate.operator.domain.repository;

import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.operator.domain.model.CategoryRelation;
import com.datamate.operator.interfaces.dto.CategoryRelationDto;
import org.apache.ibatis.annotations.Param;

import java.util.List;

public interface CategoryRelationRepository extends IRepository<CategoryRelation> {

    List<CategoryRelationDto> findAllRelation();

    void batchInsert(@Param("operatorId") String operatorId, @Param("categories") List<Integer> categories);
}
