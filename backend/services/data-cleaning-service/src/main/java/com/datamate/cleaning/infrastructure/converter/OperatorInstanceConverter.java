package com.datamate.cleaning.infrastructure.converter;


import com.datamate.cleaning.domain.model.entity.OperatorInstance;
import com.datamate.cleaning.interfaces.dto.OperatorInstanceDto;
import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.datamate.operator.domain.model.OperatorView;
import com.datamate.operator.interfaces.dto.OperatorDto;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.Named;
import org.mapstruct.factory.Mappers;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Map;

@Mapper
public interface OperatorInstanceConverter {
    OperatorInstanceConverter INSTANCE = Mappers.getMapper(OperatorInstanceConverter.class);

    ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    @Mapping(target = "settingsOverride", source = "overrides", qualifiedByName = "mapToString")
    @Mapping(target = "operatorId", source = "id")
    OperatorInstance fromDtoToEntity(OperatorInstanceDto instance);

    @Mapping(target = "overrides", source = "settingsOverride", qualifiedByName = "stringToMap")
    @Mapping(target = "id", source = "operatorId")
    OperatorInstanceDto fromEntityToDto(OperatorInstance instance);

    List<OperatorInstanceDto> fromEntityToDtoList(List<OperatorInstance> instance);

    @Named("mapToString")
    static String mapToString(Map<String, Object> objects) {
         try {
             return OBJECT_MAPPER.writeValueAsString(objects);
         } catch (JsonProcessingException e) {
             throw BusinessException.of(SystemErrorCode.UNKNOWN_ERROR);
         }
    }

    @Named("stringToMap")
    static Map<String, Object> stringToMap(String json) {
        if (json == null) {
            return Collections.emptyMap();
        }
        try {
            return OBJECT_MAPPER.readValue(json, new TypeReference<>() {});
        } catch (JsonProcessingException e) {
            throw BusinessException.of(SystemErrorCode.UNKNOWN_ERROR);
        }
    }

    @Mapping(target = "categories", source = "categories", qualifiedByName = "stringToList")
    OperatorDto fromEntityToDto(OperatorView operator);

    List<OperatorDto> fromEntityToDto(List<OperatorView> operator);

    @Named("stringToList")
    default List<String> stringToList(String input) {
        if (input == null || input.isEmpty()) {
            return Collections.emptyList();
        }
        return Arrays.stream(input.split(",")).toList();
    }
}
