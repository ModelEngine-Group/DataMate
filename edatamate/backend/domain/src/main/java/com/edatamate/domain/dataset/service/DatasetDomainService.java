package com.edatamate.domain.dataset.service;

import com.alibaba.fastjson2.JSONObject;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edatamate.common.dataset.Dataset;
import com.edatamate.common.dataset.DatasetFile;
import com.edatamate.common.dataset.DatasetStatus;
import com.edatamate.common.dataset.SrcAndDesTypeEnum;
import com.edatamate.common.dataset.dto.DatasetPageQueryDto;
import com.edatamate.common.dataset.utils.LocalScannerUtils;
import com.edatamate.common.schedule.SimpleCronTask;
import com.edatamate.domain.dataset.parser.datasetconfig.SyncConfig;
import com.edatamate.domain.dataset.repository.DatasetFileRepository;
import com.edatamate.domain.dataset.repository.DatasetRepository;
import com.edatamate.domain.dataset.schedule.ScheduleSyncService;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.concurrent.ConcurrentHashMap;

@Service
@RequiredArgsConstructor
public class DatasetDomainService {
    private static final Logger LOGGER = LoggerFactory.getLogger(DatasetDomainService.class);

    private final DatasetRepository datasetRepository;

    private final DatasetFileRepository datasetFileRepository;

    private final ScheduleSyncService scheduleSyncService;

    private final ConcurrentHashMap<Long, SimpleCronTask> taskMap = new ConcurrentHashMap<>();

    @Value("${dataset.file.base-dir:/dataset}")
    private String baseDatasetPath;

    @PreDestroy
    public void destroyTasks() {
        for (SimpleCronTask task : taskMap.values()) {
            task.cancel();
        }
        taskMap.clear();
    }

    @PostConstruct
    public void initTasksFromDb() {
        List<Dataset> datasets = datasetRepository.list();
        for (Dataset dataset : datasets) {
            if (SrcAndDesTypeEnum.getRemoteSource().contains(dataset.getSrcType())) {
                SimpleCronTask simpleCronTask = createSyncTask(dataset);
                taskMap.put(dataset.getId(), simpleCronTask);
            }
        }
    }

    /**
     * 创建数据集
     */
    public Dataset createDataset(Dataset dataset) {
        dataset.setParentId(0L); // 默认父级ID为0
        dataset.setStatus(DatasetStatus.DRAFT);
        datasetRepository.save(dataset);
        String datasetPath = baseDatasetPath + "/" + dataset.getId();
        if (SrcAndDesTypeEnum.LOCAL.getType().equals(dataset.getDesType())) { // 如果目标类型是本地导入, 需要在后台生成一个路径存放数据集
            dataset.setDesConfig(new JSONObject().fluentPut("dest_path", datasetPath).toString());
        }
        datasetRepository.updateById(dataset);
        if (SrcAndDesTypeEnum.getRemoteSource().contains(dataset.getSrcType())) {
            SimpleCronTask simpleCronTask = createSyncTask(dataset);
            SyncConfig syncConfig = JSONObject.parseObject(dataset.getScheduleConfig(), SyncConfig.class);
            if (syncConfig.isExecuteCurrent()) {
                simpleCronTask.runOnceNow();
            }
            taskMap.put(dataset.getId(), simpleCronTask);
        }
        return dataset;
    }

    private SimpleCronTask createSyncTask(Dataset dataset) {
        Runnable job = () -> {
            try {
                // 1.下发任务到datax
                datasetRepository.submitSyncJob(dataset);
                // 2.执行扫盘逻辑
                // todo 数据库同步不需要进行扫盘；扫盘后需要注意文件差异对比，如果差异对比由datax实现，那么需要删除数据库中当前数据集的文件元数据
                String datasetPath = baseDatasetPath + "/" + dataset.getId();
                List<DatasetFile> datasetFiles = LocalScannerUtils.scanDatasetFiles(datasetPath, dataset.getId());
                // 3.保存文件元数据
                datasetFileRepository.saveBatch(datasetFiles, 1000);
            } catch (Exception e) {
                LOGGER.warn("Error executing sync job for dataset: {}", dataset.getId(), e);
            }
        };
        SyncConfig syncConfig = JSONObject.parseObject(dataset.getScheduleConfig(), SyncConfig.class);
        syncConfig.toCronFromFixed();
        return scheduleSyncService.addScheduleCornTask(job, syncConfig);
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
     *
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
