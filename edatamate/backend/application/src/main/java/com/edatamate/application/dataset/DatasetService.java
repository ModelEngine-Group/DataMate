package com.edatamate.application.dataset;

import com.alibaba.fastjson2.JSONObject;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edatamate.application.datax.DataXHandler;
import com.edatamate.common.dataset.Dataset;
import com.edatamate.common.dataset.DatasetStatus;
import com.edatamate.common.dataset.SrcAndDesTypeEnum;
import com.edatamate.common.dataset.dto.DatasetPageQueryDto;
import com.edatamate.domain.repository.DatasetRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.UUID;

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

    private final DataXHandler dataXHandler;

    @Value("${dataset.file.base-dir:/dataset}")
    private String baseDatasetPath;

    /**
     * 创建数据集
     */
    public Dataset createDataset(Dataset dataset) {
        dataset.setParentId(0L); // 默认父级ID为0
        dataset.setStatus(DatasetStatus.DRAFT);
        String sourceType = dataset.getSrcType();
        String destinationType = dataset.getDesType();
        if ("local".equals(destinationType)) { // 如果目标类型是本地导入, 需要在后台生成一个路径存放数据集
            String destPath = baseDatasetPath + "/" + dataset.getName();
            dataset.setDesConfig(new JSONObject().fluentPut("dest_path", destPath).toString());
        }
        if (SrcAndDesTypeEnum.getRemoteSource().contains(sourceType)) {
            dataXHandler.createJob(dataset.getSrcConfig(), dataset.getDesConfig(), sourceType, destinationType);
        }
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
