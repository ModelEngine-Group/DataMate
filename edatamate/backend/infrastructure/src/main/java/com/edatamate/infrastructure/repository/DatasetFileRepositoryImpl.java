package com.edatamate.infrastructure.repository;

import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.edatamate.common.dataset.DatasetFile;
import com.edatamate.domain.dataset.repository.DatasetFileRepository;
import com.edatamate.infrastructure.mapper.DatasetFileMapper;
import org.springframework.stereotype.Repository;

import java.util.List;

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
        lambdaUpdate().eq(DatasetFile::getDatasetId, datasetId).remove();
    }

    @Override
    public List<String> getFilePathsByIds(List<Long> fileIds) {
        return lambdaQuery().in(DatasetFile::getId, fileIds).list().stream().map(DatasetFile::getPath).toList();
    }
}
