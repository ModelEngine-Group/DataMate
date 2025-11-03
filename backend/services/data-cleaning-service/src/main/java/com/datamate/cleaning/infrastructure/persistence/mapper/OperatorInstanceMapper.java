package com.datamate.cleaning.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.cleaning.domain.model.entity.OperatorInstance;
import org.apache.ibatis.annotations.Mapper;


@Mapper
public interface OperatorInstanceMapper extends BaseMapper<OperatorInstance> {
}
