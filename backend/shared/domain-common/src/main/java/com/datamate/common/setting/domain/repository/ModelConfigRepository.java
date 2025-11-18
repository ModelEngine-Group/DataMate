package com.datamate.common.setting.domain.repository;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.common.setting.domain.entity.ModelConfig;
import com.datamate.common.setting.domain.entity.ModelType;
import com.datamate.common.setting.interfaces.rest.dto.QueryModelRequest;

/**
 * 模型配置仓库接口
 *
 * @author dallas
 * @since 2025-10-27
 */
public interface ModelConfigRepository extends IRepository<ModelConfig> {
    /**
     * 分页查询模型配置
     *
     * @param queryModelRequest 分页查询参数
     * @return 模型配置列表
     */
    IPage<ModelConfig> page(QueryModelRequest queryModelRequest);

    void saveAndSetDefault(ModelConfig modelConfig);

    void removeDefault(ModelType type);

    void updateAndSetDefault(ModelConfig modelConfig, Boolean isDefault);
}
