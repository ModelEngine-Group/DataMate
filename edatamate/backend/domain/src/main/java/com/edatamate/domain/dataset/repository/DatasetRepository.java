package com.edatamate.domain.dataset.repository;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.edatamate.common.dataset.Dataset;
import com.edatamate.common.dataset.dto.DatasetPageQueryDto;

/**
 * 数据集仓储层接口
 *
 * @author: dallas
 * @since: 2025-07-14
 */
public interface DatasetRepository extends IRepository<Dataset> {
    /**
     * 分页查询数据集
     *
     * @param dto 数据集分页查询参数DTO
     * @return 分页结果，包含数据集列表和分页信息
     */
    IPage<Dataset> pageQuery(DatasetPageQueryDto dto);
}
