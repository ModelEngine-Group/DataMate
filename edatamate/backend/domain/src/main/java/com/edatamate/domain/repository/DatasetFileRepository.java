package com.edatamate.domain.repository;

import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.edatamate.common.dataset.DatasetFile;

public interface DatasetFileRepository extends IRepository<DatasetFile> {
    void removeByDatasetId(Long datasetId);
}
