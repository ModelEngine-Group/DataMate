package com.datamate.operator.infrastructure.persistence.Impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.operator.domain.contants.OperatorConstant;
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
    public void batchInsert(String operatorId, List<String> categories) {
        List<CategoryRelation> categoryRelations = categories.stream()
            .map(category -> new CategoryRelation(category, operatorId))
            .toList();
        mapper.insert(categoryRelations);
    }

    @Override
    public void batchUpdate(String operatorId, List<String> categories) {
        List<CategoryRelation> categoryRelations = categories.stream()
                .map(category -> new CategoryRelation(category, operatorId))
                .toList();
        LambdaQueryWrapper<CategoryRelation> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(CategoryRelation::getOperatorId, operatorId);
        mapper.delete(queryWrapper);
        mapper.insert(categoryRelations);
    }

    @Override
    public void deleteByOperatorId(String operatorId) {
        LambdaQueryWrapper<CategoryRelation> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(CategoryRelation::getOperatorId, operatorId);
        mapper.delete(queryWrapper);
    }

    @Override
    public boolean operatorIsPredefined(String operatorId) {
        LambdaQueryWrapper<CategoryRelation> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(CategoryRelation::getOperatorId, operatorId)
                .eq(CategoryRelation::getCategoryId, OperatorConstant.CATEGORY_PREDEFINED_ID);
        return this.exists(queryWrapper);
    }
}
