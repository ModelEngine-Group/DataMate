package com.dataengine.datamanagement.application.service;

import com.dataengine.datamanagement.domain.model.dataset.*;
import com.dataengine.datamanagement.domain.repository.DatasetRepository;
import com.dataengine.datamanagement.domain.repository.TagRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

/**
 * 数据集应用服务
 */
@Service
@Transactional
public class DatasetApplicationService {

    private final DatasetRepository datasetRepository;
    private final TagRepository tagRepository;

    @Autowired
    public DatasetApplicationService(DatasetRepository datasetRepository, TagRepository tagRepository) {
        this.datasetRepository = datasetRepository;
        this.tagRepository = tagRepository;
    }

    /**
     * 创建数据集
     */
    public Dataset createDataset(String name, String description, String typeCode, String typeName,
                               String typeDescription, List<String> tagNames, String dataSource,
                               String targetLocation, String createdBy) {
        
        // 检查名称是否已存在
        if (datasetRepository.findByName(name).isPresent()) {
            throw new IllegalArgumentException("Dataset with name '" + name + "' already exists");
        }

        // 创建数据集
        DatasetType datasetType = new DatasetType(typeCode, typeName, typeDescription);
        String datasetId = UUID.randomUUID().toString();
        Dataset dataset = new Dataset(datasetId, name, description, datasetType, 
                                    dataSource, targetLocation, createdBy);

        // 处理标签
        if (tagNames != null && !tagNames.isEmpty()) {
            Set<Tag> tags = processTagNames(tagNames);
            tags.forEach(dataset::addTag);
        }

        return datasetRepository.save(dataset);
    }

    /**
     * 更新数据集
     */
    public Dataset updateDataset(String datasetId, String name, String description, 
                               List<String> tagNames, DatasetStatus status) {
        Dataset dataset = datasetRepository.findById(datasetId)
            .orElseThrow(() -> new IllegalArgumentException("Dataset not found: " + datasetId));

        // 更新基本信息
        if (name != null || description != null) {
            dataset.updateBasicInfo(name, description);
        }

        // 更新状态
        if (status != null) {
            dataset.updateStatus(status);
        }

        // 更新标签
        if (tagNames != null) {
            // 清除现有标签并减少使用计数
            dataset.getTags().forEach(Tag::decrementUsage);
            dataset.getTags().clear();
            
            // 添加新标签
            if (!tagNames.isEmpty()) {
                Set<Tag> newTags = processTagNames(tagNames);
                newTags.forEach(dataset::addTag);
            }
        }

        return datasetRepository.save(dataset);
    }

    /**
     * 删除数据集
     */
    public void deleteDataset(String datasetId) {
        Dataset dataset = datasetRepository.findById(datasetId)
            .orElseThrow(() -> new IllegalArgumentException("Dataset not found: " + datasetId));

        // 减少标签使用计数
        dataset.getTags().forEach(Tag::decrementUsage);

        datasetRepository.delete(dataset);
    }

    /**
     * 获取数据集详情
     */
    @Transactional(readOnly = true)
    public Dataset getDataset(String datasetId) {
        return datasetRepository.findById(datasetId)
            .orElseThrow(() -> new IllegalArgumentException("Dataset not found: " + datasetId));
    }

    /**
     * 分页查询数据集
     */
    @Transactional(readOnly = true)
    public Page<Dataset> getDatasets(String typeCode, DatasetStatus status, String keyword,
                                   List<String> tagNames, Pageable pageable) {
        return datasetRepository.findByCriteria(typeCode, status, keyword, tagNames, pageable);
    }

    /**
     * 获取数据集统计信息
     */
    @Transactional(readOnly = true)
    public DatasetStatistics getDatasetStatistics(String datasetId) {
        Dataset dataset = getDataset(datasetId);
        
        Map<String, Integer> fileTypeDistribution = new HashMap<>();
        Map<String, Integer> statusDistribution = new HashMap<>();
        
        for (DatasetFile file : dataset.getFiles()) {
            // 文件类型分布
            fileTypeDistribution.merge(file.getFileType(), 1, Integer::sum);
            
            // 状态分布
            statusDistribution.merge(file.getStatus().name(), 1, Integer::sum);
        }
        
        return new DatasetStatistics(
            dataset.getFileCount(),
            (int) dataset.getFiles().stream().filter(f -> f.getStatus() == DatasetFileStatus.COMPLETED).count(),
            dataset.getTotalSize(),
            dataset.getCompletionRate(),
            fileTypeDistribution,
            statusDistribution
        );
    }

    /**
     * 处理标签名称，创建或获取标签
     */
    private Set<Tag> processTagNames(List<String> tagNames) {
        Set<Tag> tags = new HashSet<>();
        
        for (String tagName : tagNames) {
            Tag tag = tagRepository.findByName(tagName)
                .orElseGet(() -> {
                    String tagId = UUID.randomUUID().toString();
                    Tag newTag = new Tag(tagId, tagName, "#007bff", null);
                    return tagRepository.save(newTag);
                });
            
            tag.incrementUsage();
            tags.add(tag);
        }
        
        return tags;
    }

    /**
     * 数据集统计信息
     */
    public static class DatasetStatistics {
        private final Integer totalFiles;
        private final Integer completedFiles;
        private final Long totalSize;
        private final Float completionRate;
        private final Map<String, Integer> fileTypeDistribution;
        private final Map<String, Integer> statusDistribution;

        public DatasetStatistics(Integer totalFiles, Integer completedFiles, Long totalSize,
                               Float completionRate, Map<String, Integer> fileTypeDistribution,
                               Map<String, Integer> statusDistribution) {
            this.totalFiles = totalFiles;
            this.completedFiles = completedFiles;
            this.totalSize = totalSize;
            this.completionRate = completionRate;
            this.fileTypeDistribution = fileTypeDistribution;
            this.statusDistribution = statusDistribution;
        }

        // Getters
        public Integer getTotalFiles() { return totalFiles; }
        public Integer getCompletedFiles() { return completedFiles; }
        public Long getTotalSize() { return totalSize; }
        public Float getCompletionRate() { return completionRate; }
        public Map<String, Integer> getFileTypeDistribution() { return fileTypeDistribution; }
        public Map<String, Integer> getStatusDistribution() { return statusDistribution; }
    }
}
