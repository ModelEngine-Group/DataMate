package com.datamate.operator.domain.repository;

import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.operator.domain.model.Category;
import com.datamate.operator.interfaces.dto.CategoryDto;

import java.util.List;

public interface CategoryRepository extends IRepository<Category> {
    List<CategoryDto> findAllCategories();
}
