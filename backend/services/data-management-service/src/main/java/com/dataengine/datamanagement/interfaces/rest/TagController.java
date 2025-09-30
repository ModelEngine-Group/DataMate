package com.dataengine.datamanagement.interfaces.rest;

import com.dataengine.datamanagement.application.service.TagApplicationService;
import com.dataengine.datamanagement.domain.model.dataset.Tag;
import com.dataengine.datamanagement.interfaces.api.TagApi;
import com.dataengine.datamanagement.interfaces.dto.CreateTagRequest;
import com.dataengine.datamanagement.interfaces.dto.TagResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 标签 REST 控制器（UUID 模式）
 */
@RestController
public class TagController implements TagApi {

    private final TagApplicationService tagApplicationService;

    @Autowired
    public TagController(TagApplicationService tagApplicationService) {
        this.tagApplicationService = tagApplicationService;
    }

    @Override
    public ResponseEntity<List<TagResponse>> getTags(String keyword) {
        List<Tag> tags = tagApplicationService.searchTags(keyword);

        List<TagResponse> response = tags.stream()
            .map(this::convertToResponse)
            .collect(Collectors.toList());

        return ResponseEntity.ok(response);
    }

    @Override
    public ResponseEntity<TagResponse> createTag(CreateTagRequest createTagRequest) {
        try {
            Tag tag = tagApplicationService.createTag(
                createTagRequest.getName(),
                createTagRequest.getColor(),
                createTagRequest.getDescription()
            );

            return ResponseEntity.status(HttpStatus.CREATED).body(convertToResponse(tag));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().build();
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
