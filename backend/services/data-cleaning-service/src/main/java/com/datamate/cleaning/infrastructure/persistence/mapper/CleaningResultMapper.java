package com.datamate.cleaning.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.cleaning.domain.model.entity.CleaningResult;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface CleaningResultMapper extends BaseMapper<CleaningResult> {
}
