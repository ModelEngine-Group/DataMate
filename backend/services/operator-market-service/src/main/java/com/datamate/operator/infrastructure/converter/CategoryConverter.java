package com.datamate.operator.infrastructure.converter;

import com.datamate.operator.domain.model.Category;
import com.datamate.operator.interfaces.dto.CategoryDto;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

import java.util.List;

@Mapper
public interface CategoryConverter {
    CategoryConverter INSTANCE = Mappers.getMapper(CategoryConverter.class);

    List<CategoryDto> fromEntityToDto (List<Category> dto);
}
