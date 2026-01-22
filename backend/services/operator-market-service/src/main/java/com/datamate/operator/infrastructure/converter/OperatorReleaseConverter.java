package com.datamate.operator.infrastructure.converter;

import com.datamate.operator.domain.model.OperatorRelease;
import com.datamate.operator.interfaces.dto.OperatorReleaseDto;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

import java.util.List;

@Mapper
public interface OperatorReleaseConverter {
    OperatorReleaseConverter INSTANCE = Mappers.getMapper(OperatorReleaseConverter.class);

    List<OperatorReleaseDto> fromEntityToDto(List<OperatorRelease> dto);

    OperatorRelease fromDtoToEntity(OperatorReleaseDto dto);
}
