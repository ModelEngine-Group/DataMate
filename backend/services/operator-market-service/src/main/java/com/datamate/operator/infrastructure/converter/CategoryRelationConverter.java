package com.datamate.operator.infrastructure.converter;

import com.datamate.operator.domain.model.CategoryRelation;
import com.datamate.operator.interfaces.dto.CategoryRelationDto;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

import java.util.List;

@Mapper
public interface CategoryRelationConverter {
    CategoryRelationConverter INSTANCE = Mappers.getMapper(CategoryRelationConverter.class);

    List<CategoryRelationDto> fromEntityToDto (List<CategoryRelation> dto);
}
