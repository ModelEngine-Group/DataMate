package com.dataengine.datamanagement.application.service;

import com.dataengine.datamanagement.domain.model.dataset.Tag;
import com.dataengine.datamanagement.domain.repository.TagRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

/**
 * 标签应用服务
 */
@Service
@Transactional
public class TagApplicationService {

    private final TagRepository tagRepository;

    @Autowired
    public TagApplicationService(TagRepository tagRepository) {
        this.tagRepository = tagRepository;
    }

    /**
     * 创建标签
     */
    public Tag createTag(String name, String color, String description) {
        // 检查名称是否已存在
        if (tagRepository.findByName(name).isPresent()) {
            throw new IllegalArgumentException("Tag with name '" + name + "' already exists");
        }

        String tagId = UUID.randomUUID().toString();
        Tag tag = new Tag(tagId, name, color, description);
        
        return tagRepository.save(tag);
    }

    /**
     * 获取所有标签
     */
    @Transactional(readOnly = true)
    public List<Tag> getAllTags() {
        return tagRepository.findAllByOrderByUsageCountDesc();
    }

    /**
     * 根据关键词搜索标签
     */
    @Transactional(readOnly = true)
    public List<Tag> searchTags(String keyword) {
        if (keyword == null || keyword.trim().isEmpty()) {
            return getAllTags();
        }
        return tagRepository.findByKeyword(keyword.trim());
    }

    /**
     * 获取标签详情
     */
    @Transactional(readOnly = true)
    public Tag getTag(String tagId) {
        return tagRepository.findById(tagId)
            .orElseThrow(() -> new IllegalArgumentException("Tag not found: " + tagId));
    }

    /**
     * 根据名称获取标签
     */
    @Transactional(readOnly = true)
    public Tag getTagByName(String name) {
        return tagRepository.findByName(name)
            .orElseThrow(() -> new IllegalArgumentException("Tag not found: " + name));
    }
}
