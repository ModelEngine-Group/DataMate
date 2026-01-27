package com.datamate.common.infrastructure.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.common.domain.model.LineageEdge;
import com.datamate.common.infrastructure.config.IgnoreDataScopeAnnotation;
import org.apache.ibatis.annotations.Mapper;

/**
 * 边映射器接口
 *
 * @since 2026/1/23
 */
@Mapper
@IgnoreDataScopeAnnotation
public interface LineageEdgeMapper extends BaseMapper<LineageEdge> {
}
