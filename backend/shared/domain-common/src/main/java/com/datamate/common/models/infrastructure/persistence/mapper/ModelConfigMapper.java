package com.datamate.common.models.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.common.models.domain.entity.ModelConfig;
import org.apache.ibatis.annotations.Mapper;

/**
 * 模型配置映射器接口
 *
 * @author dallas
 * @since 2025-10-27
 */
@Mapper
public interface ModelConfigMapper extends BaseMapper<ModelConfig> {
}