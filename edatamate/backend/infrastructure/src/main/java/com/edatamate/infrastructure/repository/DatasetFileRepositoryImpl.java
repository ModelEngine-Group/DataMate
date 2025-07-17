package com.edatamate.infrastructure.repository;

import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.edatamate.common.dataset.DatasetFile;
import com.edatamate.domain.repository.DatasetFileRepository;
import com.edatamate.infrastructure.mapper.DatasetFileMapper;
import org.springframework.stereotype.Repository;

/**
 * 数据集文件仓储层实现类
 *
 * @author: dallas
 * @since: 2025-07-16
 */
@Repository
public class DatasetFileRepositoryImpl extends CrudRepository<DatasetFileMapper, DatasetFile> implements DatasetFileRepository {

    @Override
    public void removeByDatasetId(Long datasetId) {
        lambdaUpdate()
                .eq(DatasetFile::getDatasetId, datasetId)
                .remove();
    }
}
