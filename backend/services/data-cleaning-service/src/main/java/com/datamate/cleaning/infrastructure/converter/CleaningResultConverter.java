package com.datamate.cleaning.infrastructure.converter;

import com.datamate.cleaning.domain.model.entity.CleaningResult;
import com.datamate.cleaning.interfaces.dto.CleaningResultDto;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

import java.util.List;

@Mapper
public interface CleaningResultConverter {
    CleaningResultConverter INSTANCE = Mappers.getMapper(CleaningResultConverter.class);

    List<CleaningResultDto> convertEntityToDto(List<CleaningResult> cleaningResult);
}
