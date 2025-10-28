package com.datamate.operator.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.operator.domain.model.Operator;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface OperatorMapper extends BaseMapper<Operator> {
}
