package com.dataengine.datamanagement.interfaces.rest;

import com.dataengine.common.interfaces.Response;
import com.dataengine.datamanagement.application.service.TagApplicationService;
import com.dataengine.datamanagement.domain.model.dataset.Tag;
import com.dataengine.datamanagement.interfaces.dto.CreateTagRequest;
import com.dataengine.datamanagement.interfaces.dto.TagResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 标签 REST 控制器（UUID 模式）
 */
@RestController
@RequestMapping("/data-management/tags")
public class TagController {

    private final TagApplicationService tagApplicationService;

    @Autowired
    public TagController(TagApplicationService tagApplicationService) {
        this.tagApplicationService = tagApplicationService;
    }

    /**
     * 查询标签列表
     */
    @GetMapping
    public ResponseEntity<Response<List<TagResponse>>> getTags(@RequestParam(required = false) String keyword) {
        List<Tag> tags = tagApplicationService.searchTags(keyword);
        List<TagResponse> response = tags.stream()
            .map(this::convertToResponse)
            .collect(Collectors.toList());
        return ResponseEntity.ok(Response.ok(response));
    }

    /**
     * 创建标签
     */
    @PostMapping
    public ResponseEntity<Response<TagResponse>> createTag(@RequestBody CreateTagRequest createTagRequest) {
        try {
            Tag tag = tagApplicationService.createTag(
                createTagRequest.getName(),
                createTagRequest.getColor(),
                createTagRequest.getDescription()
            );
            return ResponseEntity.status(201).body(Response.ok(convertToResponse(tag)));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Response.error(e.getMessage(), null));
        }
    }

    private TagResponse convertToResponse(Tag tag) {
        TagResponse response = new TagResponse();
        response.setId(tag.getId());
        response.setName(tag.getName());
        response.setColor(tag.getColor());
        response.setDescription(tag.getDescription());
        response.setUsageCount(tag.getUsageCount() != null ? tag.getUsageCount().intValue() : null);
        return response;
    }
}
