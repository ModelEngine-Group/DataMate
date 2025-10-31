package com.datamate.cleaning.infrastructure.converter;


import com.datamate.cleaning.domain.model.entity.OperatorInstance;
import com.datamate.cleaning.domain.model.entity.Operator;
import com.datamate.cleaning.interfaces.dto.OperatorInstanceDto;
import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.datamate.operator.interfaces.dto.OperatorDto;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.Named;
import org.mapstruct.factory.Mappers;

import java.util.List;
import java.util.Map;

@Mapper
public interface OperatorInstanceConverter {
    OperatorInstanceConverter INSTANCE = Mappers.getMapper(OperatorInstanceConverter.class);

    @Mapping(target = "settingsOverride", source = "overrides", qualifiedByName = "mapToString")
    @Mapping(target = "operatorId", source = "id")
    OperatorInstance fromDtoToEntity(OperatorInstanceDto instance);

    @Named("mapToString")
    static String mapToString(Map<String, Object> objects) {
         ObjectMapper objectMapper = new ObjectMapper();
         try {
             return objectMapper.writeValueAsString(objects);
         } catch (JsonProcessingException e) {
             throw BusinessException.of(SystemErrorCode.UNKNOWN_ERROR);
         }
    }

    List<OperatorDto> fromEntityToDto(List<Operator> operator);
}
