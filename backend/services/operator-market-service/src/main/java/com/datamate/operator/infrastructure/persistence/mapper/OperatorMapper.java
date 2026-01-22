package com.datamate.operator.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.common.infrastructure.config.IgnoreDataScopeAnnotation;
import com.datamate.operator.domain.model.Operator;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface OperatorMapper extends BaseMapper<Operator> {

    @IgnoreDataScopeAnnotation
    @Select("SELECT count(1) FROM t_operator_instance oi JOIN t_clean_template t ON oi.instance_id = t.id " +
            "WHERE oi.operator_id = #{operatorId}")
    int operatorInTemplate(String operatorId);

    @IgnoreDataScopeAnnotation
    @Select("SELECT count(1) FROM t_operator_instance oi JOIN t_clean_task t ON oi.instance_id = t.id " +
            "WHERE oi.operator_id = #{operatorId} AND t.status != 'COMPLETED'")
    int operatorInUnstopTask(String operatorId);
}
