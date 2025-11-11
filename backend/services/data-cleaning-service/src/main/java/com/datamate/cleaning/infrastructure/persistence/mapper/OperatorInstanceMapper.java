package com.datamate.cleaning.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.cleaning.domain.model.entity.Operator;
import com.datamate.cleaning.domain.model.entity.OperatorInstance;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

import java.util.List;


@Mapper
public interface OperatorInstanceMapper extends BaseMapper<OperatorInstance> {
    @Select("SELECT id, name, description, version, inputs, outputs, runtime, settings, created_at, updated_at " +
            "FROM t_operator_instance toi LEFT JOIN datamate.t_operator o ON toi.operator_id = o.id " +
            "WHERE toi.instance_id = #{instanceId} ORDER BY toi.op_index")
    List<Operator> findOperatorByInstanceId(String instanceId);
}
