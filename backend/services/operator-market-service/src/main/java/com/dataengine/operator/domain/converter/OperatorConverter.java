package com.dataengine.operator.domain.converter;

import com.dataengine.operator.domain.modal.Operator;
import com.dataengine.operator.interfaces.dto.OperatorResponse;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

@Mapper
public interface OperatorConverter {
    OperatorConverter INSTANCE = Mappers.getMapper(OperatorConverter.class);

    OperatorResponse operatorToResponse(Operator operator);
}
