package com.edatamate.domain.dataset.service;

import com.alibaba.fastjson2.JSONObject;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edatamate.common.dataset.Dataset;
import com.edatamate.common.dataset.DatasetStatus;
import com.edatamate.common.dataset.SrcAndDesTypeEnum;
import com.edatamate.common.dataset.dto.DatasetPageQueryDto;
import com.edatamate.common.schedule.SimpleCronTask;
import com.edatamate.domain.dataset.parser.datasetconfig.SyncConfig;
import com.edatamate.domain.dataset.repository.DatasetRepository;
import com.edatamate.domain.dataset.schedule.ScheduleSyncService;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.concurrent.ConcurrentHashMap;

@Service
@RequiredArgsConstructor
public class DatasetDomainService {
    private static final Logger LOGGER = LoggerFactory.getLogger(DatasetDomainService.class);

    private final DatasetRepository datasetRepository;

    private final ScheduleSyncService scheduleSyncService;

    private final ConcurrentHashMap<Long, SimpleCronTask> taskMap = new ConcurrentHashMap<>();

    /**
     * 创建数据集
     */
    public Dataset createDataset(Dataset dataset) {
        dataset.setParentId(0L); // 默认父级ID为0
        dataset.setStatus(DatasetStatus.DRAFT);
        datasetRepository.save(dataset);
        if (SrcAndDesTypeEnum.getRemoteSource().contains(dataset.getSrcType())) {
            // todo 下发同步任务
            Runnable job = () -> {
                try {
                    // 添加具体的同步逻辑
                    // 1.下发任务到datax
                    datasetRepository.submitSyncJob(dataset);
                    // 2.执行扫盘逻辑
                } catch (Exception e) {
                    LOGGER.warn("Error executing sync job for dataset: {}", dataset.getId(), e);
                }
            };
            SyncConfig syncConfig = JSONObject.parseObject(dataset.getScheduleConfig(), SyncConfig.class);
            SimpleCronTask simpleCronTask = scheduleSyncService.addScheduleCornTask(job, syncConfig);
            taskMap.put(dataset.getId(), simpleCronTask);
        }
        return dataset;
    }

    /**
     * 根据数据集id查询数据集
     */
    public Dataset getDatasetById(Long datasetId) {
        return datasetRepository.getById(datasetId);
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
     * @param datasetId 数据集ID
     */
    public void deleteDataset(Long datasetId) {
        datasetRepository.removeById(datasetId);
        taskMap.remove(datasetId);
    }

    /**
     * 分页条件查询数据集
     */
    public IPage<Dataset> pageQuery(DatasetPageQueryDto queryDto) {
        return datasetRepository.pageQuery(queryDto);
    }
}
