package com.datamate.common.setting.infrastructure.persistence.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.common.setting.domain.entity.ModelConfig;
import com.datamate.common.setting.domain.entity.ModelType;
import com.datamate.common.setting.domain.repository.ModelConfigRepository;
import com.datamate.common.setting.infrastructure.persistence.mapper.ModelConfigMapper;
import com.datamate.common.setting.interfaces.rest.dto.QueryModelRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.Objects;

/**
 * 模型配置仓库实现类
 *
 * @author dallas
 * @since 2025-10-27
 */
@Repository
@RequiredArgsConstructor
public class ModelConfigRepositoryImpl extends CrudRepository<ModelConfigMapper, ModelConfig> implements ModelConfigRepository {
    private final ModelConfigMapper modelConfigMapper;


    @Override
    public IPage<ModelConfig> page(QueryModelRequest queryModelRequest) {
        IPage<ModelConfig> page = new Page<>(queryModelRequest.getPage(), queryModelRequest.getSize());
        return this.page(page, new LambdaQueryWrapper<ModelConfig>()
                .eq(StringUtils.hasText(queryModelRequest.getProvider()), ModelConfig::getProvider, queryModelRequest.getProvider())
                .eq(Objects.nonNull(queryModelRequest.getType()), ModelConfig::getType, queryModelRequest.getType())
                .eq(Objects.nonNull(queryModelRequest.getIsEnabled()), ModelConfig::getIsEnabled, queryModelRequest.getIsEnabled())
                .eq(Objects.nonNull(queryModelRequest.getIsDefault()), ModelConfig::getIsDefault, queryModelRequest.getIsDefault()));
    }

    @Transactional
    public void saveAndSetDefault(ModelConfig modelConfig) {
        LambdaQueryWrapper<ModelConfig> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(ModelConfig::getType, modelConfig.getType()).eq(ModelConfig::getIsDefault, true);
        if (this.getOne(queryWrapper) == null) {
            modelConfig.setIsDefault(true);
        } else {
            removeDefault(modelConfig.getType());
        }
        super.save(modelConfig);
    }

    public void removeDefault(ModelType type) {
        LambdaUpdateWrapper<ModelConfig> updateWrapper = new LambdaUpdateWrapper<>();
        updateWrapper.set(ModelConfig::getIsDefault, false)
                .eq(ModelConfig::getType, type)
                .eq(ModelConfig::getIsDefault, true);
        this.update(updateWrapper);
    }

    @Transactional
    public void updateAndSetDefault(ModelConfig modelConfig, Boolean isDefault) {
        if (!modelConfig.getIsDefault() && isDefault) {
            removeDefault(modelConfig.getType());
        }
        modelConfig.setIsDefault(isDefault);
        this.updateById(modelConfig);
    }
}
