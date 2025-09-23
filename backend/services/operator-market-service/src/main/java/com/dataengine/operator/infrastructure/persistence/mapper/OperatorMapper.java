package com.dataengine.operator.infrastructure.persistence.mapper;

import com.dataengine.operator.domain.modal.Operator;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface OperatorMapper {
    List<Operator> findAllOperators();
}
