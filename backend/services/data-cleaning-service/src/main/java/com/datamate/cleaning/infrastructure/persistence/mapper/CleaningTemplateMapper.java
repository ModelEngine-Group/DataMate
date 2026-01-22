package com.datamate.cleaning.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.toolkit.Constants;
import com.datamate.cleaning.domain.model.entity.TemplateWithInstance;
import com.datamate.cleaning.domain.model.entity.CleaningTemplate;
import com.datamate.common.infrastructure.config.IgnoreDataScopeAnnotation;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
@IgnoreDataScopeAnnotation
public interface CleaningTemplateMapper extends BaseMapper<CleaningTemplate> {
    @Select("SELECT t.id AS id, name, description, created_at, updated_at, created_by, operator_id, op_index, " +
        "settings_override FROM t_clean_template t LEFT JOIN t_operator_instance o ON t.id = o.instance_id " +
        "${ew.customSqlSegment}")
    List<TemplateWithInstance> findAllTemplates(@Param(Constants.WRAPPER) Wrapper<TemplateWithInstance> queryWrapper);
}
