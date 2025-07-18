package com.edatamate.application.dataset;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edatamate.common.dataset.Dataset;
import com.edatamate.common.dataset.DatasetStatus;
import com.edatamate.common.dataset.dto.DatasetPageQueryDto;
import com.edatamate.domain.repository.DatasetRepository;
import com.edatamate.infrastructure.mapper.DatasetMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

/**
 * 数据集服务
 *
 * @author: dallas
 * @since: 2025-07-15
 */
@Service
@RequiredArgsConstructor
public class DatasetService {
    private final DatasetRepository datasetRepository;

    private final DatasetFileService datasetFileService;

    /**
     * 新增数据集
     */
    public Dataset createDataset(Dataset dataset) {
        dataset.setParentId(0L); // 默认父级ID为0
        dataset.setStatus(DatasetStatus.DRAFT);
        datasetRepository.save(dataset);
        return dataset;
    }

    /**
     * 根据ID查询数据集
     */
    public Dataset getDatasetById(Long id) {
        return datasetRepository.getById(id);
    }

    /**
     * 更新数据集
     */
    public Dataset updateDataset(Dataset dataset) {
        datasetRepository.updateById(dataset);
        return dataset;
    }

    /**
     * 删除数据集
     */
    public void deleteDataset(Long id) {
        datasetRepository.removeById(id);
        datasetFileService.deleteDatasetFiles(id);
    }

    /**
     * 分页条件查询数据集
     */
    public IPage<Dataset> pageQuery(DatasetPageQueryDto queryDto) {
        return datasetRepository.pageQuery(queryDto);
    }
}
