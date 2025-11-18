package com.datamate.common.setting.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.common.setting.domain.entity.SysParam;
import org.apache.ibatis.annotations.Mapper;

/**
 * 系统参数映射器
 *
 * @author dallas
 * @since 2025-11-04
 */
@Mapper
public interface SysParamMapper extends BaseMapper<SysParam> {
}
