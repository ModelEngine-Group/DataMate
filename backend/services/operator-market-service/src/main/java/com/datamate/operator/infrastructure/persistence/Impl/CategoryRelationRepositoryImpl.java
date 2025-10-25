package com.datamate.operator.infrastructure.persistence.Impl;

import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.operator.domain.model.CategoryRelation;
import com.datamate.operator.domain.repository.CategoryRelationRepository;
import com.datamate.operator.infrastructure.converter.CategoryRelationConverter;
import com.datamate.operator.infrastructure.persistence.mapper.CategoryRelationMapper;
import com.datamate.operator.interfaces.dto.CategoryRelationDto;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
@RequiredArgsConstructor
public class CategoryRelationRepositoryImpl extends CrudRepository<CategoryRelationMapper, CategoryRelation>
    implements CategoryRelationRepository {
    private final CategoryRelationMapper mapper;

    @Override
    public List<CategoryRelationDto> findAllRelation() {
        return CategoryRelationConverter.INSTANCE.fromEntityToDto(mapper.selectList(null));
    }

    @Override
    public void batchInsert(String operatorId, List<Integer> categories) {
        List<CategoryRelation> categoryRelations = categories.stream()
            .map(category -> new CategoryRelation(category, operatorId))
            .toList();
        mapper.insert(categoryRelations);
    }
}
