package com.datamate.operator.infrastructure.persistence.Impl;

import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.operator.domain.model.Category;
import com.datamate.operator.domain.repository.CategoryRepository;
import com.datamate.operator.infrastructure.converter.CategoryConverter;
import com.datamate.operator.infrastructure.persistence.mapper.CategoryMapper;
import com.datamate.operator.interfaces.dto.CategoryDto;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
@RequiredArgsConstructor
public class CategoryRepositoryImpl extends CrudRepository<CategoryMapper, Category> implements CategoryRepository {
    private final CategoryMapper mapper;


    @Override
    public List<CategoryDto> findAllCategories() {
        return CategoryConverter.INSTANCE.fromEntityToDto(mapper.selectList(null));
    }
}
