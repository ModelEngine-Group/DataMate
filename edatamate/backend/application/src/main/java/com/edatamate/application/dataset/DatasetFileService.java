package com.edatamate.application.dataset;

import com.edatamate.common.dataset.DatasetFile;
import com.edatamate.domain.repository.DatasetFileRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class DatasetFileService {
    private final DatasetFileRepository datasetFileRepository;

    /**
     * 根据ID查询数据集文件
     *
     * @param id 数据集文件ID
     * @return 数据集文件
     */
    public DatasetFile getDatasetFileById(Long id) {
        return datasetFileRepository.getById(id);
    }

    /**
     * 新增数据集文件
     *
     * @param datasetFile 数据集文件
     * @return 数据集文件
     */
    public DatasetFile createDatasetFile(DatasetFile datasetFile) {
        datasetFileRepository.save(datasetFile);
        return datasetFile;
    }

    /**
     * 更新数据集文件
     *
     * @param datasetFile 数据集文件
     * @return 更新后的数据集文件
     */
    public DatasetFile updateDatasetFile(DatasetFile datasetFile) {
        datasetFileRepository.updateById(datasetFile);
        return datasetFile;
    }

    /**
     * 删除数据集文件
     *
     * @param id 数据集文件ID
     */
    public void deleteDatasetFile(Long id) {
        datasetFileRepository.removeById(id);
    }
}
