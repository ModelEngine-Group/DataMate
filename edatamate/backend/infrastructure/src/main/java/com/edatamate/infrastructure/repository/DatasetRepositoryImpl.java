package com.edatamate.infrastructure.repository;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.edatamate.common.dataset.Dataset;
import com.edatamate.common.dataset.SrcAndDesTypeEnum;
import com.edatamate.domain.dataset.repository.DatasetRepository;
import com.edatamate.infrastructure.datax.DataXHandler;
import com.edatamate.infrastructure.mapper.DatasetMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Repository;
import com.edatamate.common.dataset.dto.DatasetPageQueryDto;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import org.springframework.util.StringUtils;

/**
 * 数据集repository实现
 *
 * @author: dallas
 * @since: 2025-07-14
 */
@Repository
public class DatasetRepositoryImpl extends CrudRepository<DatasetMapper, Dataset> implements DatasetRepository {
    @Autowired
    private DataXHandler dataXHandler;

    @Override
    public IPage<Dataset> pageQuery(DatasetPageQueryDto dto) {
        Page<Dataset> page = new Page<>(dto.pageNum(), dto.pageSize());
        LambdaQueryWrapper<Dataset> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(dto.name())) {
            wrapper.like(Dataset::getName, dto.name());
        }
        if (dto.type() != null) {
            wrapper.eq(Dataset::getType, dto.type());
        }
        if (dto.status() != null) {
            wrapper.eq(Dataset::getStatus, dto.status());
        }
        if (StringUtils.hasText(dto.createdBy())) {
            wrapper.eq(Dataset::getCreatedBy, dto.createdBy());
        }
        // 可补充其他条件
        page.setTotal(baseMapper.selectCount(wrapper));
        return baseMapper.selectPage(page, wrapper);
    }

    @Override
    public void submitSyncJob(Dataset dataset) {
        String srcType = dataset.getSrcType();
        if (SrcAndDesTypeEnum.getRemoteSource().contains(srcType)) {
            dataXHandler.createJob(dataset.getSrcConfig(), dataset.getDesConfig(), srcType, dataset.getDesType());
        }
    }
}
