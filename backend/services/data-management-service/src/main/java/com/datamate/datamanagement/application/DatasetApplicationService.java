package com.datamate.datamanagement.application;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.datamate.common.domain.utils.ChunksSaver;
import com.datamate.datamanagement.interfaces.dto.*;
import com.datamate.common.infrastructure.exception.BusinessAssert;
import com.datamate.common.interfaces.PagedResponse;
import com.datamate.datamanagement.domain.model.dataset.Dataset;
import com.datamate.datamanagement.domain.model.dataset.DatasetFile;
import com.datamate.datamanagement.domain.model.dataset.Tag;
import com.datamate.datamanagement.infrastructure.client.CollectionTaskClient;
import com.datamate.datamanagement.infrastructure.client.dto.CollectionTaskDetailResponse;
import com.datamate.datamanagement.infrastructure.client.dto.LocalCollectionConfig;
import com.datamate.datamanagement.infrastructure.exception.DataManagementErrorCode;
import com.datamate.datamanagement.infrastructure.persistence.mapper.TagMapper;
import com.datamate.datamanagement.infrastructure.persistence.repository.DatasetFileRepository;
import com.datamate.datamanagement.infrastructure.persistence.repository.DatasetRepository;
import com.datamate.datamanagement.interfaces.converter.DatasetConverter;
import com.datamate.datamanagement.interfaces.dto.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * 数据集应用服务（对齐 DB schema，使用 UUID 字符串主键）
 */
@Slf4j
@Service
@Transactional
@RequiredArgsConstructor
public class DatasetApplicationService {
    private final DatasetRepository datasetRepository;
    private final TagMapper tagMapper;
    private final DatasetFileRepository datasetFileRepository;
    private final CollectionTaskClient collectionTaskClient;
    private final FileMetadataService fileMetadataService;
    private final ObjectMapper objectMapper;

    @Value("${dataset.base.path:/dataset}")
    private String datasetBasePath;

    /**
     * 创建数据集
     */
    @Transactional
    public Dataset createDataset(CreateDatasetRequest createDatasetRequest) {
        BusinessAssert.isTrue(datasetRepository.findByName(createDatasetRequest.getName()) == null, DataManagementErrorCode.DATASET_ALREADY_EXISTS);
        // 创建数据集对象
        Dataset dataset = DatasetConverter.INSTANCE.convertToDataset(createDatasetRequest);
        dataset.initCreateParam(datasetBasePath);
        // 处理标签
        Set<Tag> processedTags = Optional.ofNullable(createDatasetRequest.getTags())
            .filter(CollectionUtils::isNotEmpty)
            .map(this::processTagNames)
            .orElseGet(HashSet::new);
        dataset.setTags(processedTags);
        datasetRepository.save(dataset);

        //todo 需要解耦这块逻辑
        if (StringUtils.hasText(createDatasetRequest.getDataSource())) {
            // 数据源id不为空，使用异步线程进行文件扫盘落库
            processDataSourceAsync(dataset.getId(), createDatasetRequest.getDataSource());
        }
        return dataset;
    }

    public Dataset updateDataset(String datasetId, UpdateDatasetRequest updateDatasetRequest) {
        Dataset dataset = datasetRepository.getById(datasetId);
        BusinessAssert.notNull(dataset, DataManagementErrorCode.DATASET_NOT_FOUND);
        if (StringUtils.hasText(updateDatasetRequest.getName())) {
            dataset.setName(updateDatasetRequest.getName());
        }
        if (StringUtils.hasText(updateDatasetRequest.getDescription())) {
            dataset.setDescription(updateDatasetRequest.getDescription());
        }
        if (CollectionUtils.isNotEmpty(updateDatasetRequest.getTags())) {
            dataset.setTags(processTagNames(updateDatasetRequest.getTags()));
        }
        if (Objects.nonNull(updateDatasetRequest.getStatus())) {
            dataset.setStatus(updateDatasetRequest.getStatus());
        }
        if (StringUtils.hasText(updateDatasetRequest.getDataSource())) {
            // 数据源id不为空，使用异步线程进行文件扫盘落库
            processDataSourceAsync(dataset.getId(), updateDatasetRequest.getDataSource());
        }
        datasetRepository.updateById(dataset);
        return dataset;
    }

    /**
     * 删除数据集
     */
    @Transactional
    public void deleteDataset(String datasetId) {
        Dataset dataset = datasetRepository.getById(datasetId);
        datasetRepository.removeById(datasetId);
        if (dataset != null) {
            ChunksSaver.deleteFolder(dataset.getPath());
        }
    }

    /**
     * 获取数据集详情
     */
    @Transactional(readOnly = true)
    public Dataset getDataset(String datasetId) {
        Dataset dataset = datasetRepository.getById(datasetId);
        BusinessAssert.notNull(dataset, DataManagementErrorCode.DATASET_NOT_FOUND);
        List<DatasetFile> datasetFiles = datasetFileRepository.findAllByDatasetId(datasetId);
        dataset.setFiles(datasetFiles);
        return dataset;
    }

    /**
     * 分页查询数据集
     */
    @Transactional(readOnly = true)
    public PagedResponse<DatasetResponse> getDatasets(DatasetPagingQuery query) {
        IPage<Dataset> page = new Page<>(query.getPage(), query.getSize());
        page = datasetRepository.findByCriteria(page, query);
        return PagedResponse.of(DatasetConverter.INSTANCE.convertToResponse(page.getRecords()), page.getCurrent(), page.getTotal(), page.getPages());
    }

    /**
     * 处理标签名称，创建或获取标签
     */
    private Set<Tag> processTagNames(List<String> tagNames) {
        Set<Tag> tags = new HashSet<>();
        for (String tagName : tagNames) {
            Tag tag = tagMapper.findByName(tagName);
            if (tag == null) {
                Tag newTag = new Tag(tagName, null, null, "#007bff");
                newTag.setUsageCount(0L);
                newTag.setId(UUID.randomUUID().toString());
                tagMapper.insert(newTag);
                tag = newTag;
            }
            tag.setUsageCount(tag.getUsageCount() == null ? 1L : tag.getUsageCount() + 1);
            tagMapper.updateUsageCount(tag.getId(), tag.getUsageCount());
            tags.add(tag);
        }
        return tags;
    }

    /**
     * 获取数据集统计信息
     */
    @Transactional(readOnly = true)
    public Map<String, Object> getDatasetStatistics(String datasetId) {
        Dataset dataset = datasetRepository.getById(datasetId);
        if (dataset == null) {
            throw new IllegalArgumentException("Dataset not found: " + datasetId);
        }

        Map<String, Object> statistics = new HashMap<>();

        // 基础统计
        Long totalFiles = datasetFileRepository.countByDatasetId(datasetId);
        Long completedFiles = datasetFileRepository.countCompletedByDatasetId(datasetId);
        Long totalSize = datasetFileRepository.sumSizeByDatasetId(datasetId);

        statistics.put("totalFiles", totalFiles != null ? totalFiles.intValue() : 0);
        statistics.put("completedFiles", completedFiles != null ? completedFiles.intValue() : 0);
        statistics.put("totalSize", totalSize != null ? totalSize : 0L);

        // 完成率计算
        float completionRate = 0.0f;
        if (totalFiles != null && totalFiles > 0) {
            completionRate = (completedFiles != null ? completedFiles.floatValue() : 0.0f) / totalFiles.floatValue() * 100.0f;
        }
        statistics.put("completionRate", completionRate);

        // 文件类型分布统计
        Map<String, Integer> fileTypeDistribution = new HashMap<>();
        List<DatasetFile> allFiles = datasetFileRepository.findAllByDatasetId(datasetId);
        if (allFiles != null) {
            for (DatasetFile file : allFiles) {
                String fileType = file.getFileType() != null ? file.getFileType() : "unknown";
                fileTypeDistribution.put(fileType, fileTypeDistribution.getOrDefault(fileType, 0) + 1);
            }
        }
        statistics.put("fileTypeDistribution", fileTypeDistribution);

        // 状态分布统计
        Map<String, Integer> statusDistribution = new HashMap<>();
        if (allFiles != null) {
            for (DatasetFile file : allFiles) {
                String status = file.getStatus() != null ? file.getStatus() : "unknown";
                statusDistribution.put(status, statusDistribution.getOrDefault(status, 0) + 1);
            }
        }
        statistics.put("statusDistribution", statusDistribution);

        return statistics;
    }

    /**
     * 获取所有数据集的汇总统计信息
     */
    public AllDatasetStatisticsResponse getAllDatasetStatistics() {
        return datasetRepository.getAllDatasetStatistics();
    }

    /**
     * 异步处理数据源文件扫描
     *
     * @param datasetId    数据集ID
     * @param dataSourceId 数据源ID（归集任务ID）
     */
    @Async
    public void processDataSourceAsync(String datasetId, String dataSourceId) {
        try {
            log.info("开始处理数据源文件扫描，数据集ID: {}, 数据源ID: {}", datasetId, dataSourceId);
            List<String> filePaths = getFilePaths(dataSourceId);
            if (CollectionUtils.isEmpty(filePaths)) {
                return;
            }
            log.info("开始扫描文件，共 {} 个文件路径", filePaths.size());

            List<DatasetFile> datasetFiles = fileMetadataService.scanFiles(filePaths, datasetId);
            // 查询数据集中已存在的文件
            List<DatasetFile> existDatasetFileList = datasetFileRepository.findAllByDatasetId(datasetId);
            Map<String, DatasetFile> existDatasetFilePathMap = existDatasetFileList.stream().collect(Collectors.toMap(DatasetFile::getFilePath, Function.identity()));
            Dataset dataset = datasetRepository.getById(datasetId);
            dataset.setFiles(existDatasetFileList);

            // 批量同步数据集文件表
            asyncDatasetFile(datasetFiles, existDatasetFilePathMap, dataset, existDatasetFileList, filePaths);
            datasetRepository.updateById(dataset);
        } catch (Exception e) {
            log.error("处理数据源文件扫描失败，数据集ID: {}, 数据源ID: {}", datasetId, dataSourceId, e);
        }
    }

    private void asyncDatasetFile(List<DatasetFile> datasetFiles, Map<String, DatasetFile> existDatasetFilePathMap, Dataset dataset, List<DatasetFile> existDatasetFileList, List<String> filePaths) {
        if (CollectionUtils.isNotEmpty(datasetFiles)) {
            for (DatasetFile datasetFile : datasetFiles) {
                if (existDatasetFilePathMap.containsKey(datasetFile.getFilePath())) {
                    DatasetFile existDatasetFile = existDatasetFilePathMap.get(datasetFile.getFilePath());
                    dataset.removeFile(existDatasetFile);
                    existDatasetFile.setFileSize(datasetFile.getFileSize());
                    dataset.addFile(existDatasetFile);
                    dataset.active();
                    datasetFileRepository.updateById(existDatasetFile);
                } else {
                    dataset.addFile(datasetFile);
                    dataset.active();
                    datasetFileRepository.save(datasetFile);
                }
            }
            log.info("文件元数据写入完成，共写入 {} 条记录", datasetFiles.size());
        } else {
            log.warn("未扫描到有效文件");
        }
        for (DatasetFile datasetFile : existDatasetFileList) {
            String existFilePath = datasetFile.getFilePath();
            for (String filePath : filePaths) {
                if (existFilePath.equals(filePath) || existFilePath.startsWith(filePath)) {
                    if (Files.notExists(Paths.get(existFilePath))) {
                        dataset.removeFile(datasetFile);
                        datasetFileRepository.removeById(datasetFile.getId());
                    }
                }
            }
        }
    }

    private List<String> getFilePaths(String dataSourceId) {
        CollectionTaskDetailResponse taskDetail = collectionTaskClient.getTaskDetail(dataSourceId).getData();
        if (taskDetail == null) {
            log.warn("获取归集任务详情失败，任务ID: {}", dataSourceId);
            return Collections.emptyList();
        }
        log.info("获取到归集任务详情: {}", taskDetail);
        return Collections.singletonList(taskDetail.getTargetPath());
    }

    /**
     * 解析任务配置
     */
    private LocalCollectionConfig parseTaskConfig(Map<String, Object> configMap) {
        try {
            if (configMap == null || configMap.isEmpty()) {
                return null;
            }
            return objectMapper.convertValue(configMap, LocalCollectionConfig.class);
        } catch (Exception e) {
            log.error("解析任务配置失败", e);
            return null;
        }
    }
}
