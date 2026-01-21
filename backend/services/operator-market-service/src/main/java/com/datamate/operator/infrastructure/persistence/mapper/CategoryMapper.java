package com.datamate.operator.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.common.infrastructure.config.IgnoreDataScopeAnnotation;
import com.datamate.operator.domain.model.Category;
import org.apache.ibatis.annotations.Mapper;

@Mapper
@IgnoreDataScopeAnnotation
public interface CategoryMapper extends BaseMapper<Category> {
}
