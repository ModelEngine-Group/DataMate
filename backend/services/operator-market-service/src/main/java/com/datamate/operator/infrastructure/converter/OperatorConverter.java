package com.datamate.operator.infrastructure.converter;

import com.datamate.operator.domain.model.Operator;
import com.datamate.operator.domain.model.OperatorView;
import com.datamate.operator.interfaces.dto.OperatorDto;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.Named;
import org.mapstruct.factory.Mappers;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

@Mapper
public interface OperatorConverter {
    OperatorConverter INSTANCE = Mappers.getMapper(OperatorConverter.class);

    @Mapping(target = "categories", source = "categories", qualifiedByName = "stringToList")
    OperatorDto fromEntityToDto(OperatorView operator);

    @Named("stringToList")
    static List<Integer> stringToList(String input) {
        if (input == null || input.isEmpty()) {
            return Collections.emptyList();
        }
        return Arrays.stream(input.split(",")).map(Integer::valueOf).toList();
    }

    Operator fromDtoToEntity(OperatorDto operator);
}
