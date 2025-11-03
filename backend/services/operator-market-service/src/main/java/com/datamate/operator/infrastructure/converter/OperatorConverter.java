package com.datamate.operator.infrastructure.converter;

import com.datamate.common.domain.model.ChunkUploadRequest;
import com.datamate.operator.domain.model.Operator;
import com.datamate.operator.domain.model.OperatorView;
import com.datamate.operator.interfaces.dto.OperatorDto;
import com.datamate.operator.interfaces.dto.UploadOperatorRequest;
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

    List<OperatorDto> fromEntityToDto(List<Operator> operator);

    @Named("stringToList")
    static List<String> stringToList(String input) {
        if (input == null || input.isEmpty()) {
            return Collections.emptyList();
        }
        return Arrays.stream(input.split(",")).map(String::valueOf).toList();
    }

    Operator fromDtoToEntity(OperatorDto operator);

    ChunkUploadRequest toChunkRequest(UploadOperatorRequest request);
}
