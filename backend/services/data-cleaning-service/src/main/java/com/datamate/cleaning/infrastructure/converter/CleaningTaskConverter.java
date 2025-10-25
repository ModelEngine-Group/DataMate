package com.datamate.cleaning.infrastructure.converter;

import com.datamate.cleaning.domain.model.entity.CleaningTask;
import com.datamate.cleaning.interfaces.dto.CleaningTaskDto;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

import java.util.List;

@Mapper
public interface CleaningTaskConverter {
    CleaningTaskConverter INSTANCE = Mappers.getMapper(CleaningTaskConverter.class);

    CleaningTaskDto fromEntityToDto(CleaningTask source);

    List<CleaningTaskDto> fromEntityToDto(List<CleaningTask> source);

    CleaningTask fromDtoToEntity(CleaningTaskDto source);
}
