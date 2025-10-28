package com.datamate.cleaning.infrastructure.converter;

import com.datamate.cleaning.domain.model.entity.CleaningTemplate;
import com.datamate.cleaning.interfaces.dto.CleaningTemplateDto;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

@Mapper
public interface CleaningTemplateConverter {
    CleaningTemplateConverter INSTANCE = Mappers.getMapper(CleaningTemplateConverter.class);

    CleaningTemplate fromDtoToEntity(CleaningTemplateDto dto);

    CleaningTemplateDto fromEntityToDto(CleaningTemplate entity);
}
