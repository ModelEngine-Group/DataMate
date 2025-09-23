package com.dataengine.operator.infrastructure.persistence.mapper;

import com.dataengine.operator.domain.modal.Category;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface CategoryMapper {

    List<Category> findAllCategories();
}
