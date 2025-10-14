package com.dataengine.datamanagement.application.service;

import com.dataengine.datamanagement.domain.model.dataset.Dataset;
import com.dataengine.datamanagement.domain.model.dataset.DatasetFile;
import com.dataengine.datamanagement.domain.model.dataset.Tag;
import com.dataengine.datamanagement.infrastructure.client.CollectionTaskClient;
import com.dataengine.datamanagement.infrastructure.client.dto.CollectionTaskDetailResponse;
import com.dataengine.datamanagement.infrastructure.client.dto.LocalCollectionConfig;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.DatasetFileMapper;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.DatasetMapper;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.TagMapper;
import com.dataengine.datamanagement.interfaces.converter.DatasetConverter;
import com.dataengine.datamanagement.interfaces.dto.AllDatasetStatisticsResponse;
import com.dataengine.datamanagement.interfaces.dto.CreateDatasetRequest;
import com.dataengine.datamanagement.interfaces.dto.DatasetPagingQuery;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.commons.lang3.StringUtils;
import org.apache.ibatis.session.RowBounds;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.*;

/**
 * 数据集应用服务（对齐 DB schema，使用 UUID 字符串主键）
 */
@Slf4j
@Service
@Transactional
public class DatasetApplicationService {

    private final DatasetMapper datasetMapper;
    private final TagMapper tagMapper;
    private final DatasetFileMapper datasetFileMapper;
    private final CollectionTaskClient collectionTaskClient;
    private final FileMetadataService fileMetadataService;
    private final ObjectMapper objectMapper;

    @Value("${dataset.base.path:/dataset}")
    private String datasetBasePath;

    @Autowired
    public DatasetApplicationService(DatasetMapper datasetMapper,
                                     TagMapper tagMapper,
                                     DatasetFileMapper datasetFileMapper,
                                     CollectionTaskClient collectionTaskClient,
                                     FileMetadataService fileMetadataService,
                                     ObjectMapper objectMapper) {
        this.datasetMapper = datasetMapper;
        this.tagMapper = tagMapper;
        this.datasetFileMapper = datasetFileMapper;
        this.collectionTaskClient = collectionTaskClient;
        this.fileMetadataService = fileMetadataService;
        this.objectMapper = objectMapper;
    }

    /**
     * 创建数据集
     */
    @Transactional
    public Dataset createDataset(CreateDatasetRequest createDatasetRequest) {
        if (datasetMapper.findByName(createDatasetRequest.getName()) != null) {
            throw new IllegalArgumentException("Dataset with name '" + createDatasetRequest.getName() + "' already exists");
        }

        // 创建数据集对象
        Dataset dataset = DatasetConverter.INSTANCE.convertToDataset(createDatasetRequest);
        dataset.initCreateParam(datasetBasePath);
        datasetMapper.insert(dataset);

        // 处理标签
        Set<Tag> processedTags = new HashSet<>();
        if (CollectionUtils.isNotEmpty(createDatasetRequest.getTags())) {
            processedTags = processTagNames(createDatasetRequest.getTags());
            for (Tag t : processedTags) {
                tagMapper.insertDatasetTag(dataset.getId(), t.getId());
            }
        }

        if (StringUtils.isNotBlank(createDatasetRequest.getDataSource())) {
            // 数据源id不为空，使用异步线程进行文件扫盘落库
            processDataSourceAsync(dataset.getId(), createDatasetRequest.getDataSource());
        }

        // 返回创建的数据集，包含标签信息
        Dataset createdDataset = datasetMapper.findById(dataset.getId());
        createdDataset.getTags().addAll(processedTags);
        return createdDataset;
    }

    /**
     * 更新数据集
     */
    public Dataset updateDataset(String datasetId, String name, String description,
                                 List<String> tagNames, String status) {
        Dataset dataset = datasetMapper.findById(datasetId);
        if (dataset == null) {
            throw new IllegalArgumentException("Dataset not found: " + datasetId);
        }

        if (name != null && !name.isEmpty()) dataset.setName(name);
        if (description != null) dataset.setDescription(description);
        if (status != null && !status.isEmpty()) dataset.setStatus(status);
        dataset.setUpdatedAt(LocalDateTime.now());

        Set<Tag> processedTags = new HashSet<>();
        if (tagNames != null) {
            tagMapper.deleteDatasetTagsByDatasetId(datasetId);
            if (!tagNames.isEmpty()) {
                processedTags = processTagNames(tagNames);
                for (Tag t : processedTags) {
                    tagMapper.insertDatasetTag(datasetId, t.getId());
                }
            }
        } else {
            // 如果没有传入标签参数，保持原有标签
            List<Tag> existingTags = tagMapper.findByDatasetId(datasetId);
            if (existingTags != null) {
                processedTags.addAll(existingTags);
            }
        }

        datasetMapper.update(dataset);

        // 返回更新后的数据集，包含标签信息
        Dataset updatedDataset = datasetMapper.findById(datasetId);
        updatedDataset.getTags().addAll(processedTags);
        return updatedDataset;
    }

    /**
     * 删除数据集
     */
    public void deleteDataset(String datasetId) {
        Dataset dataset = datasetMapper.findById(datasetId);
        if (dataset == null) {
            throw new IllegalArgumentException("Dataset not found: " + datasetId);
        }
        tagMapper.deleteDatasetTagsByDatasetId(datasetId);
        datasetMapper.deleteById(datasetId);
    }

    /**
     * 获取数据集详情
     */
    @Transactional(readOnly = true)
    public Dataset getDataset(String datasetId) {
        Dataset dataset = datasetMapper.findById(datasetId);
        if (dataset == null) {
            throw new IllegalArgumentException("Dataset not found: " + datasetId);
        }
        // 载入标签
        List<Tag> tags = tagMapper.findByDatasetId(datasetId);
        if (tags != null) {
            dataset.getTags().addAll(tags);
        }
        return dataset;
    }

    /**
     * 分页查询数据集
     */
    @Transactional(readOnly = true)
    public Page<Dataset> getDatasets(DatasetPagingQuery query) {
        RowBounds bounds = new RowBounds(query.getPage() * query.getSize(), query.getSize());
        List<Dataset> content = datasetMapper.findByCriteria(query.getType(), query.getStatus(), query.getKeyword(), query.getTagList(), bounds);
        long total = datasetMapper.countByCriteria(query.getType(), query.getStatus(), query.getKeyword(), query.getTagList());

        // 为每个数据集填充标签信息
        if (CollectionUtils.isNotEmpty(content)) {
            for (Dataset dataset : content) {
                List<Tag> tags = tagMapper.findByDatasetId(dataset.getId());
                if (tags != null) {
                    dataset.getTags().addAll(tags);
                }
            }
        }
        return new PageImpl<>(content, PageRequest.of(query.getPage(), query.getSize()), total);
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
        Dataset dataset = datasetMapper.findById(datasetId);
        if (dataset == null) {
            throw new IllegalArgumentException("Dataset not found: " + datasetId);
        }

        Map<String, Object> statistics = new HashMap<>();

        // 基础统计
        Long totalFiles = datasetFileMapper.countByDatasetId(datasetId);
        Long completedFiles = datasetFileMapper.countCompletedByDatasetId(datasetId);
        Long totalSize = datasetFileMapper.sumSizeByDatasetId(datasetId);

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
        List<com.dataengine.datamanagement.domain.model.dataset.DatasetFile> allFiles = datasetFileMapper.findAllByDatasetId(datasetId);
        if (allFiles != null) {
            for (com.dataengine.datamanagement.domain.model.dataset.DatasetFile file : allFiles) {
                String fileType = file.getFileType() != null ? file.getFileType() : "unknown";
                fileTypeDistribution.put(fileType, fileTypeDistribution.getOrDefault(fileType, 0) + 1);
            }
        }
        statistics.put("fileTypeDistribution", fileTypeDistribution);

        // 状态分布统计
        Map<String, Integer> statusDistribution = new HashMap<>();
        if (allFiles != null) {
            for (com.dataengine.datamanagement.domain.model.dataset.DatasetFile file : allFiles) {
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
        return datasetMapper.getAllDatasetStatistics();
    }

    /**
     * 异步处理数据源文件扫描
     * @param datasetId 数据集ID
     * @param dataSourceId 数据源ID（归集任务ID）
     */
    @Async
    public void processDataSourceAsync(String datasetId, String dataSourceId) {
        try {
            log.info("开始处理数据源文件扫描，数据集ID: {}, 数据源ID: {}", datasetId, dataSourceId);

            // 1. 调用数据归集服务获取任务详情
            CollectionTaskDetailResponse taskDetail = collectionTaskClient.getTaskDetail(dataSourceId);
            if (taskDetail == null) {
                log.error("获取归集任务详情失败，任务ID: {}", dataSourceId);
                return;
            }

            log.info("获取到归集任务详情: {}", taskDetail.getName());

            // 2. 解析任务配置
            LocalCollectionConfig config = parseTaskConfig(taskDetail.getConfig());
            if (config == null) {
                log.error("解析任务配置失败，任务ID: {}", dataSourceId);
                return;
            }

            // 3. 检查任务类型是否为 LOCAL_COLLECTION
            if (!"LOCAL_COLLECTION".equalsIgnoreCase(config.getType())) {
                log.info("任务类型不是 LOCAL_COLLECTION，跳过文件扫描。任务类型: {}", config.getType());
                return;
            }

            // 4. 获取文件路径列表
            List<String> filePaths = config.getFilePaths();
            if (CollectionUtils.isEmpty(filePaths)) {
                log.warn("文件路径列表为空，任务ID: {}", dataSourceId);
                return;
            }

            log.info("开始扫描文件，共 {} 个文件路径", filePaths.size());

            // 5. 扫描文件元数据
            List<DatasetFile> datasetFiles = fileMetadataService.scanFiles(filePaths, datasetId);

            // 6. 批量插入数据集文件表
            if (CollectionUtils.isNotEmpty(datasetFiles)) {
                for (DatasetFile datasetFile : datasetFiles) {
                    datasetFileMapper.insert(datasetFile);
                }
                log.info("文件元数据写入完成，共写入 {} 条记录", datasetFiles.size());
            } else {
                log.warn("未扫描到有效文件");
            }

        } catch (Exception e) {
            log.error("处理数据源文件扫描失败，数据集ID: {}, 数据源ID: {}", datasetId, dataSourceId, e);
        }
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
