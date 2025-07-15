package com.edatamate.infrastructure.repository;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edatamate.common.dataset.Dataset;
import com.edatamate.domain.repository.DatasetRepository;
import com.edatamate.infrastructure.mapper.DatasetMapper;
import org.springframework.stereotype.Repository;

/**
 * 数据集repository实现
 *
 * @author: dallas
 * @since: 2025-07-14
 */
@Repository
public class DatasetRepositoryImpl extends ServiceImpl<DatasetMapper, Dataset> implements DatasetRepository {
}
