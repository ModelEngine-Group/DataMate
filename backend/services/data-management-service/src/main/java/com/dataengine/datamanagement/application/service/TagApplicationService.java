package com.dataengine.datamanagement.application.service;

import com.dataengine.datamanagement.domain.model.dataset.Tag;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.TagMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.CollectionUtils;

import java.util.List;
import java.util.UUID;

/**
 * 标签应用服务（UUID 主键）
 */
@Service
@Transactional
public class TagApplicationService {

    private final TagMapper tagMapper;

    @Autowired
    public TagApplicationService(TagMapper tagMapper) {
        this.tagMapper = tagMapper;
    }

    /**
     * 创建标签
     */
    public Tag createTag(String name, String color, String description) {
        // 检查名称是否已存在
        if (tagMapper.findByName(name) != null) {
            throw new IllegalArgumentException("Tag with name '" + name + "' already exists");
        }

        Tag tag = new Tag(name, description, null, color);
        tag.setUsageCount(0L);
        tag.setId(UUID.randomUUID().toString());
        tagMapper.insert(tag);
        return tagMapper.findById(tag.getId());
    }

    /**
     * 更新标签
     *
     * @param tag 待更新的标签实体，必须包含有效的 ID
     * @return 更新结果
     */
    @Transactional
    public Tag updateTag(Tag tag) {
        Tag existingTag = tagMapper.findById(tag.getId());
        if (existingTag == null) {
            throw new IllegalArgumentException("Tag not found: " + tag.getId());
        }
        existingTag.setName(tag.getName());
        existingTag.setColor(tag.getColor());
        existingTag.setDescription(tag.getDescription());
        tagMapper.update(existingTag);
        return tagMapper.findById(existingTag.getId());
    }

    @Transactional
    public void deleteTag(List<String> tagIds) {
        List<Tag> tags = tagMapper.findByIdIn(tagIds);
        if (tags.stream().anyMatch(tag -> tag.getUsageCount() > 0)) {
            throw new IllegalArgumentException("Cannot delete tags that are in use");
        }
        if (CollectionUtils.isEmpty(tags)) {
            return;
        }
        tagMapper.deleteTagsById(tags.stream().map(Tag::getId).toList());
    }

    /**
     * 获取所有标签
     */
    @Transactional(readOnly = true)
    public List<Tag> getAllTags() {
        return tagMapper.findAllByOrderByUsageCountDesc();
    }

    /**
     * 根据关键词搜索标签
     */
    @Transactional(readOnly = true)
    public List<Tag> searchTags(String keyword) {
        if (keyword == null || keyword.trim().isEmpty()) {
            return getAllTags();
        }
        return tagMapper.findByKeyword(keyword.trim());
    }

    /**
     * 获取标签详情
     */
    @Transactional(readOnly = true)
    public Tag getTag(String tagId) {
        Tag tag = tagMapper.findById(tagId);
        if (tag == null) {
            throw new IllegalArgumentException("Tag not found: " + tagId);
        }
        return tag;
    }

    /**
     * 根据名称获取标签
     */
    @Transactional(readOnly = true)
    public Tag getTagByName(String name) {
        Tag tag = tagMapper.findByName(name);
        if (tag == null) {
            throw new IllegalArgumentException("Tag not found: " + name);
        }
        return tag;
    }
}
