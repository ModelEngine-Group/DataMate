package com.datamate.cleaning.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.cleaning.domain.model.entity.OperatorInstance;
import com.datamate.operator.domain.model.OperatorView;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

import java.util.List;


@Mapper
public interface OperatorInstanceMapper extends BaseMapper<OperatorInstance> {
    @Select("SELECT o.operator_id as id, o.operator_name as name, description, version, inputs, outputs, runtime, " +
            "   settings, created_at, updated_at, " +
            "GROUP_CONCAT(category_id ORDER BY created_at DESC SEPARATOR ',') AS categories " +
            "FROM t_operator_instance toi LEFT JOIN v_operator o ON toi.operator_id = o.operator_id " +
            "WHERE toi.instance_id = #{instanceId} " +
            "GROUP BY o.operator_id, o.operator_name, description, version, inputs, outputs, runtime," +
            "    settings, created_at, updated_at, op_index " +
            "ORDER BY toi.op_index")
    List<OperatorView> findOperatorByInstanceId(String instanceId);
}
