package com.dataengine.cleaning.infrastructure.persistence.mapper;

import com.dataengine.cleaning.domain.model.OperatorInstancePo;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;


@Mapper
public interface OperatorInstanceMapper {

    void insertInstance(@Param("instance_id") String instance_id,
                        @Param("instances") List<OperatorInstancePo> instances);
}
