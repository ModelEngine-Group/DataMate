package com.dataengine.operator.domain.converter;

import com.dataengine.operator.domain.modal.Operator;
import com.dataengine.operator.interfaces.dto.OperatorResponse;
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
    OperatorResponse operatorToResponse(Operator operator);

    @Named("stringToList")
    static List<Integer> stringToList(String input) {
        if (input == null || input.isEmpty()) {
            return Collections.emptyList();
        }
        return Arrays.stream(input.split(",")).map(Integer::valueOf).toList();
    }
}
