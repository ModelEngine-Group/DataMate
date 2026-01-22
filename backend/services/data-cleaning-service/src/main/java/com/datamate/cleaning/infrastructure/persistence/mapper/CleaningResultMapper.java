package com.datamate.cleaning.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.cleaning.domain.model.entity.CleaningResult;
import com.datamate.common.infrastructure.config.IgnoreDataScopeAnnotation;
import org.apache.ibatis.annotations.Mapper;

@Mapper
@IgnoreDataScopeAnnotation
public interface CleaningResultMapper extends BaseMapper<CleaningResult> {
}
