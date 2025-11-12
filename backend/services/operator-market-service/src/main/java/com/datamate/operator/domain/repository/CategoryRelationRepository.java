package com.datamate.operator.domain.repository;

import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.operator.domain.model.CategoryRelation;
import com.datamate.operator.interfaces.dto.CategoryRelationDto;

import java.util.List;

public interface CategoryRelationRepository extends IRepository<CategoryRelation> {

    List<CategoryRelationDto> findAllRelation();

    void batchInsert(String operatorId, List<String> categories);

    void batchUpdate(String operatorId, List<String> categories);

    void deleteByOperatorId(String operatorId);
}
