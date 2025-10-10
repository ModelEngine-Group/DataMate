package com.dataengine.datamanagement.application.service;

import com.dataengine.datamanagement.domain.model.dataset.Dataset;
import com.dataengine.datamanagement.domain.model.dataset.StatusConstants;
import com.dataengine.datamanagement.domain.model.dataset.Tag;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.DatasetFileMapper;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.DatasetMapper;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.TagMapper;
import com.dataengine.datamanagement.interfaces.dto.AllDatasetStatisticsResponse;
import org.apache.ibatis.session.RowBounds;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 数据集应用服务（对齐 DB schema，使用 UUID 字符串主键）
 */
@Service
@Transactional
public class DatasetApplicationService {

    private final DatasetMapper datasetMapper;
    private final TagMapper tagMapper;
    private final DatasetFileMapper datasetFileMapper;

    @Autowired
    public DatasetApplicationService(DatasetMapper datasetMapper, TagMapper tagMapper, DatasetFileMapper datasetFileMapper) {
        this.datasetMapper = datasetMapper;
        this.tagMapper = tagMapper;
        this.datasetFileMapper = datasetFileMapper;
    }

    /**
     * 创建数据集
     */
    public Dataset createDataset(String name, String description, String datasetType,
                                 List<String> tagNames, Long dataSourceId,
                                 String path, String format, String createdBy) {
        if (datasetMapper.findByName(name) != null) {
            throw new IllegalArgumentException("Dataset with name '" + name + "' already exists");
        }

        Dataset dataset = new Dataset();
        dataset.setId(UUID.randomUUID().toString());
        dataset.setName(name);
        dataset.setDescription(description);
        dataset.setDatasetType(datasetType);
        dataset.setDataSourceId(dataSourceId);
        dataset.setPath(path);
        dataset.setFormat(format);
        dataset.setStatus(StatusConstants.DatasetStatuses.ACTIVE);
        dataset.setCreatedBy(createdBy);
        dataset.setUpdatedBy(createdBy);
        dataset.setCreatedAt(LocalDateTime.now());
        dataset.setUpdatedAt(LocalDateTime.now());
        datasetMapper.insert(dataset); // 手动设定 UUID 主键

        // 处理标签
        Set<Tag> processedTags = new HashSet<>();
        if (tagNames != null && !tagNames.isEmpty()) {
            processedTags = processTagNames(tagNames);
            for (Tag t : processedTags) {
                tagMapper.insertDatasetTag(dataset.getId(), t.getId());
            }
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
    public Page<Dataset> getDatasets(String typeCode, String status, String keyword,
                                   List<String> tagNames, Pageable pageable) {
        RowBounds bounds = new RowBounds(pageable.getPageNumber() * pageable.getPageSize(), pageable.getPageSize());
        List<Dataset> content = datasetMapper.findByCriteria(typeCode, status, keyword, tagNames, bounds);

        // 为每个数据集填充标签信息
        if (content != null && !content.isEmpty()) {
            for (Dataset dataset : content) {
                List<Tag> tags = tagMapper.findByDatasetId(dataset.getId());
                if (tags != null) {
                    dataset.getTags().addAll(tags);
                }
            }
        }

        long total = datasetMapper.countByCriteria(typeCode, status, keyword, tagNames);
        return new PageImpl<>(content, pageable, total);
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
}
