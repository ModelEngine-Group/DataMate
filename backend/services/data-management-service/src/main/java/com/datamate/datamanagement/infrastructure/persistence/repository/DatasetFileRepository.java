package com.datamate.datamanagement.infrastructure.persistence.repository;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.datamanagement.domain.model.dataset.DatasetFile;

import java.util.List;

/**
 * 数据集文件仓储接口
 *
 * @author dallas
 * @since 2025-10-15
 */
public interface DatasetFileRepository extends IRepository<DatasetFile> {
    Long countByDatasetId(String datasetId);

    Long countCompletedByDatasetId(String datasetId);

    Long sumSizeByDatasetId(String datasetId);

    List<DatasetFile> findAllByDatasetId(String datasetId);

    DatasetFile findByDatasetIdAndFileName(String datasetId, String fileName);

    IPage<DatasetFile> findByCriteria(String datasetId, String fileType, String status, String name,
                                      IPage<DatasetFile> page);
}
