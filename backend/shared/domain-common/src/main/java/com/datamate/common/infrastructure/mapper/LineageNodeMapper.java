package com.datamate.common.infrastructure.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.common.domain.model.LineageNode;
import com.datamate.common.infrastructure.config.IgnoreDataScopeAnnotation;
import org.apache.ibatis.annotations.Mapper;

/**
 * 节点映射器接口
 *
 * @since 2026/1/23
 */
@Mapper
@IgnoreDataScopeAnnotation
public interface LineageNodeMapper extends BaseMapper<LineageNode> {
}
