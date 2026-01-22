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
        "settings, is_star, file_size, usage_count, created_at, updated_at, created_by, updated_by, " +
        "STRING_AGG(CAST(category_id AS TEXT), ',' ORDER BY created_at DESC) AS categories " +
        "FROM v_operator ${ew.customSqlSegment}")
    IPage<OperatorView> findOperatorsByCriteria(IPage<OperatorView> page,
                                               @Param(Constants.WRAPPER) Wrapper<OperatorView> queryWrapper);

    @Select("SELECT COUNT(1) FROM (SELECT operator_id AS id, operator_name AS name, description, version, inputs, outputs, runtime, " +
            "settings, is_star, file_size, usage_count, created_at, updated_at, created_by, updated_by FROM v_operator ${ew.customSqlSegment}) AS t")
    Integer countOperatorsByCriteria(@Param(Constants.WRAPPER) Wrapper<OperatorView> queryWrapper);

    @Select("SELECT operator_id AS id, operator_name AS name, description, version, inputs, outputs, runtime, " +
        "settings, is_star, file_name, file_size, usage_count, metrics, created_at, updated_at, created_by, updated_by, " +
        "STRING_AGG(category_name, ',' ORDER BY created_at DESC) AS categories " +
        "FROM v_operator WHERE operator_id = #{id} " +
        "GROUP BY operator_id, operator_name, description, version, inputs, outputs, runtime, settings, is_star, " +
            "file_name, file_size, usage_count, metrics, created_at, updated_at, created_by, updated_by")
    OperatorView findOperatorById(@Param("id") String id);
}
