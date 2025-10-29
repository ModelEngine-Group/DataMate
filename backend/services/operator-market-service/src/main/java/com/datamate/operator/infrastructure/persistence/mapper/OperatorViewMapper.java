package com.datamate.operator.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Constants;
import com.datamate.operator.domain.model.OperatorView;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;


@Mapper
public interface OperatorViewMapper extends BaseMapper<OperatorView> {
    @Select("SELECT operator_id AS id, operator_name AS name, description, version, inputs, outputs, runtime, " +
        "settings, is_star, created_at, updated_at, " +
        "GROUP_CONCAT(category_id ORDER BY created_at DESC SEPARATOR ',') AS categories " +
        "FROM v_operator ${ew.customSqlSegment}")
    IPage<OperatorView> findOperatorsByCriteria(IPage<OperatorView> page,
                                               @Param(Constants.WRAPPER) Wrapper<OperatorView> queryWrapper);

    @Select("SELECT COUNT(DISTINCT operator_id) AS count FROM v_operator ${ew.customSqlSegment}")
    Integer countOperatorsByCriteria(@Param(Constants.WRAPPER) Wrapper<OperatorView> queryWrapper);

    @Select("SELECT operator_id AS id, operator_name AS name, description, version, inputs, outputs, runtime, " +
        "settings, is_star, created_at, updated_at, " +
        "GROUP_CONCAT(category_id ORDER BY created_at DESC SEPARATOR ',') AS categories " +
        "FROM v_operator WHERE operator_id = #{id}")
    OperatorView findOperatorById(@Param("id") String id);
}
