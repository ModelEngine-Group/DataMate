package com.edatamate.domain.dataset.repository;

import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.edatamate.common.dataset.DatasetFile;

import java.util.List;

public interface DatasetFileRepository extends IRepository<DatasetFile> {
    void removeByDatasetId(Long datasetId);

    List<String> getFilePathsByIds(List<Long> fileIds);
}
