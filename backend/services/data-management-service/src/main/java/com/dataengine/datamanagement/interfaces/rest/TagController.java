package com.dataengine.datamanagement.interfaces.rest;

import com.dataengine.common.interfaces.Response;
import com.dataengine.datamanagement.application.service.TagApplicationService;
import com.dataengine.datamanagement.domain.model.dataset.Tag;
import com.dataengine.datamanagement.interfaces.converter.TagConverter;
import com.dataengine.datamanagement.interfaces.dto.CreateTagRequest;
import com.dataengine.datamanagement.interfaces.dto.TagResponse;
import com.dataengine.datamanagement.interfaces.dto.UpdateTagRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Size;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Objects;
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
    public ResponseEntity<Response<List<TagResponse>>> getTags(@RequestParam(name = "keyword", required = false) String keyword) {
        List<Tag> tags = tagApplicationService.searchTags(keyword);
        List<TagResponse> response = tags.stream()
            .map(TagConverter.INSTANCE::convertToResponse)
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
            return ResponseEntity.ok(Response.ok(TagConverter.INSTANCE.convertToResponse(tag)));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Response.error(e.getMessage(), null));
        }
    }

    /**
     * 更新标签
     *
     * @param updateTagRequest 更新参数
     * @return 更新结果
     */
    @PutMapping
    public ResponseEntity<Response<TagResponse>> updateTag(@RequestBody @Valid UpdateTagRequest updateTagRequest) {
        Tag tag = tagApplicationService.updateTag(TagConverter.INSTANCE.updateRequestToTag(updateTagRequest));
        return ResponseEntity.ok(Response.ok(TagConverter.INSTANCE.convertToResponse(tag)));
    }

    @DeleteMapping
    public ResponseEntity<Response<Valid>> deleteTag(@RequestParam(value = "ids") @Valid @Size(max = 10) List<String> ids) {
        try {
            tagApplicationService.deleteTag(ids.stream().filter(StringUtils::isNoneBlank).distinct().toList());
            return ResponseEntity.ok(Response.ok(null));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Response.error(e.getMessage(), null));
        }
    }
}
