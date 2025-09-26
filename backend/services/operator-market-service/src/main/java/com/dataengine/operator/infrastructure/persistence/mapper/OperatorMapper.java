package com.dataengine.operator.infrastructure.persistence.mapper;

import com.dataengine.operator.domain.modal.Operator;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface OperatorMapper {
    List<Operator> findAllOperators();

    List<Operator> findOperatorsByCriteria(@Param("size") Integer size, @Param("offset") Integer offset,
                                           @Param("operatorName") String operatorName,
                                           @Param("categories") List<Integer> categories,
                                           @Param("isStar") Boolean isStar);
}
