package com.dataengine.datamanagement.interfaces.rest;

import com.dataengine.datamanagement.application.service.TagApplicationService;
import com.dataengine.datamanagement.domain.model.dataset.Tag;
import com.dataengine.datamanagement.interfaces.dto.CreateTagRequest;
import com.dataengine.datamanagement.interfaces.dto.TagResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class TagControllerTest {

    @Mock
    private TagApplicationService tagApplicationService;

    @InjectMocks
    private TagController controller;

    private Tag sampleTag;

    @BeforeEach
    void setUp() {
        sampleTag = new Tag();
        sampleTag.setId("tag-id-1");
        sampleTag.setName("sample-tag");
        sampleTag.setColor("#ff0000");
        sampleTag.setDescription("Sample tag description");
        sampleTag.setUsageCount(10L);
    }

    @Test
    @DisplayName("tagsGet: 正常搜索标签")
    void tagsGet_success() {
        // Given
        List<Tag> tags = Arrays.asList(sampleTag);
        when(tagApplicationService.searchTags("sample")).thenReturn(tags);

        // When
        ResponseEntity<List<TagResponse>> response = controller.tagsGet("sample");

        // Then
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(1, response.getBody().size());

        TagResponse tagResponse = response.getBody().get(0);
        assertEquals("tag-id-1", tagResponse.getId());
        assertEquals("sample-tag", tagResponse.getName());
        assertEquals("#ff0000", tagResponse.getColor());
        assertEquals("Sample tag description", tagResponse.getDescription());
        assertEquals(10, tagResponse.getUsageCount());

        verify(tagApplicationService).searchTags("sample");
    }

    @Test
    @DisplayName("tagsGet: 无关键词搜索全部标签")
    void tagsGet_allTags() {
        List<Tag> allTags = Arrays.asList(sampleTag);
        when(tagApplicationService.searchTags(null)).thenReturn(allTags);

        ResponseEntity<List<TagResponse>> response = controller.tagsGet(null);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(1, response.getBody().size());
        verify(tagApplicationService).searchTags(null);
    }

    @Test
    @DisplayName("tagsGet: 空结果集")
    void tagsGet_emptyResult() {
        when(tagApplicationService.searchTags("nonexistent")).thenReturn(Collections.emptyList());

        ResponseEntity<List<TagResponse>> response = controller.tagsGet("nonexistent");

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().isEmpty());
        verify(tagApplicationService).searchTags("nonexistent");
    }

    @Test
    @DisplayName("tagsPost: 正常创建标签")
    void tagsPost_success() {
        // Given
        CreateTagRequest request = new CreateTagRequest();
        request.setName("new-tag");
        request.setColor("#00ff00");
        request.setDescription("New tag description");

        when(tagApplicationService.createTag("new-tag", "#00ff00", "New tag description"))
                .thenReturn(sampleTag);

        // When
        ResponseEntity<TagResponse> response = controller.tagsPost(request);

        // Then
        assertEquals(HttpStatus.CREATED, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("tag-id-1", response.getBody().getId());
        assertEquals("sample-tag", response.getBody().getName());
        assertEquals("#ff0000", response.getBody().getColor());
        assertEquals("Sample tag description", response.getBody().getDescription());
        assertEquals(10, response.getBody().getUsageCount());

        verify(tagApplicationService).createTag("new-tag", "#00ff00", "New tag description");
    }

    @Test
    @DisplayName("tagsPost: 标签名重复时返回400")
    void tagsPost_duplicateName() {
        CreateTagRequest request = new CreateTagRequest();
        request.setName("duplicate-tag");
        request.setColor("#0000ff");
        request.setDescription("Duplicate tag");

        when(tagApplicationService.createTag("duplicate-tag", "#0000ff", "Duplicate tag"))
                .thenThrow(new IllegalArgumentException("Tag already exists"));

        ResponseEntity<TagResponse> response = controller.tagsPost(request);

        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        assertNull(response.getBody());
        verify(tagApplicationService).createTag("duplicate-tag", "#0000ff", "Duplicate tag");
    }

    @Test
    @DisplayName("tagsPost: 创建标签时处理null值")
    void tagsPost_nullValues() {
        CreateTagRequest request = new CreateTagRequest();
        request.setName("minimal-tag");
        // color和description为null

        when(tagApplicationService.createTag("minimal-tag", null, null))
                .thenReturn(sampleTag);

        ResponseEntity<TagResponse> response = controller.tagsPost(request);

        assertEquals(HttpStatus.CREATED, response.getStatusCode());
        assertNotNull(response.getBody());
        verify(tagApplicationService).createTag("minimal-tag", null, null);
    }

    @Test
    @DisplayName("convertToResponse: 正常转换标签响应")
    void convertToResponse_success() {
        // 通过public API间接测试convertToResponse方法
        when(tagApplicationService.searchTags(null)).thenReturn(Arrays.asList(sampleTag));

        ResponseEntity<List<TagResponse>> response = controller.tagsGet(null);

        TagResponse tagResponse = response.getBody().get(0);
        assertEquals("tag-id-1", tagResponse.getId());
        assertEquals("sample-tag", tagResponse.getName());
        assertEquals("#ff0000", tagResponse.getColor());
        assertEquals("Sample tag description", tagResponse.getDescription());
        assertEquals(10, tagResponse.getUsageCount());
    }

    @Test
    @DisplayName("convertToResponse: 处理null的usageCount")
    void convertToResponse_nullUsageCount() {
        Tag tagWithNullUsage = new Tag();
        tagWithNullUsage.setId("tag-id-2");
        tagWithNullUsage.setName("null-usage-tag");
        tagWithNullUsage.setUsageCount(null);

        when(tagApplicationService.searchTags(null)).thenReturn(Arrays.asList(tagWithNullUsage));

        ResponseEntity<List<TagResponse>> response = controller.tagsGet(null);

        TagResponse tagResponse = response.getBody().get(0);
        assertEquals("tag-id-2", tagResponse.getId());
        assertEquals("null-usage-tag", tagResponse.getName());
        assertNull(tagResponse.getUsageCount());
    }

    @Test
    @DisplayName("convertToResponse: 处理多个标签")
    void convertToResponse_multipleTags() {
        Tag tag1 = new Tag();
        tag1.setId("tag-1");
        tag1.setName("first-tag");
        tag1.setUsageCount(5L);

        Tag tag2 = new Tag();
        tag2.setId("tag-2");
        tag2.setName("second-tag");
        tag2.setUsageCount(15L);

        when(tagApplicationService.searchTags("multi")).thenReturn(Arrays.asList(tag1, tag2));

        ResponseEntity<List<TagResponse>> response = controller.tagsGet("multi");

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals(2, response.getBody().size());

        TagResponse first = response.getBody().get(0);
        TagResponse second = response.getBody().get(1);

        assertEquals("tag-1", first.getId());
        assertEquals("first-tag", first.getName());
        assertEquals(5, first.getUsageCount());

        assertEquals("tag-2", second.getId());
        assertEquals("second-tag", second.getName());
        assertEquals(15, second.getUsageCount());

        verify(tagApplicationService).searchTags("multi");
    }

    @Test
    @DisplayName("tagsGet: 搜索关键词为空字符串")
    void tagsGet_emptyKeyword() {
        when(tagApplicationService.searchTags("")).thenReturn(Arrays.asList(sampleTag));

        ResponseEntity<List<TagResponse>> response = controller.tagsGet("");

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals(1, response.getBody().size());
        verify(tagApplicationService).searchTags("");
    }

    @Test
    @DisplayName("tagsGet: 搜索关键词为空白字符")
    void tagsGet_blankKeyword() {
        when(tagApplicationService.searchTags("   ")).thenReturn(Arrays.asList(sampleTag));

        ResponseEntity<List<TagResponse>> response = controller.tagsGet("   ");

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertEquals(1, response.getBody().size());
        verify(tagApplicationService).searchTags("   ");
    }
}
