package com.dataengine.datamanagement.application.service;

import com.dataengine.datamanagement.domain.model.dataset.Dataset;
import com.dataengine.datamanagement.domain.model.dataset.Tag;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.DatasetFileMapper;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.DatasetMapper;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.TagMapper;
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
        dataset.setStatus("DRAFT");
        dataset.setCreatedBy(createdBy);
        dataset.setUpdatedBy(createdBy);
        dataset.setCreatedAt(LocalDateTime.now());
        dataset.setUpdatedAt(LocalDateTime.now());
        datasetMapper.insert(dataset); // 手动设定 UUID 主键

        // 处理标签
        if (tagNames != null && !tagNames.isEmpty()) {
            Set<Tag> tags = processTagNames(tagNames);
            for (Tag t : tags) {
                tagMapper.insertDatasetTag(dataset.getId(), t.getId());
            }
        }
        return datasetMapper.findById(dataset.getId());
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

        if (tagNames != null) {
            tagMapper.deleteDatasetTagsByDatasetId(datasetId);
            if (!tagNames.isEmpty()) {
                Set<Tag> newTags = processTagNames(tagNames);
                for (Tag t : newTags) {
                    tagMapper.insertDatasetTag(datasetId, t.getId());
                }
            }
        }

        datasetMapper.update(dataset);
        return datasetMapper.findById(datasetId);
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
}
