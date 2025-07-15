package com.edatamate.application.dataset;

import com.edatamate.common.dataset.Dataset;
import com.edatamate.domain.repository.DatasetRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

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

    /**
     * 获取数据集列表
     *
     * @return 数据集列表
     */
    public List<Dataset> getDatasets() {
        return datasetRepository.list();
    }
}
