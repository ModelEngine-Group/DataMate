package com.dataengine.datamanagement.interfaces.rest;

import com.dataengine.common.interfaces.PagedResponse;
import com.dataengine.common.interfaces.Response;
import com.dataengine.datamanagement.application.service.DatasetApplicationService;
import com.dataengine.datamanagement.domain.model.dataset.Dataset;
import com.dataengine.datamanagement.domain.model.dataset.StatusConstants;
import com.dataengine.datamanagement.domain.model.dataset.Tag;
import com.dataengine.datamanagement.interfaces.dto.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.time.LocalDateTime;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class DatasetControllerTest {

    @Mock
    private DatasetApplicationService datasetApplicationService;

    @InjectMocks
    private DatasetController controller;

    private Dataset sampleDataset;

    @BeforeEach
    void setUp() {
        Tag sampleTag = new Tag();
        sampleTag.setId("tag-id-1");
        sampleTag.setName("test-tag");
        sampleTag.setColor("#ff0000");
        sampleTag.setDescription("Test tag");
        sampleTag.setUsageCount(5L);

        sampleDataset = new Dataset();
        sampleDataset.setId("dataset-id-1");
        sampleDataset.setName("Test Dataset");
        sampleDataset.setDescription("Test description");
        sampleDataset.setDatasetType("CSV");
        sampleDataset.setStatus(StatusConstants.DatasetStatuses.ACTIVE);
        sampleDataset.setDataSourceId("1L");
        sampleDataset.setPath("/test/path");
        sampleDataset.setFileCount(10L);
        sampleDataset.setSizeBytes(1024L);
        sampleDataset.setCompletionRate(80.0);
        sampleDataset.setCreatedAt(LocalDateTime.now());
        sampleDataset.setUpdatedAt(LocalDateTime.now());
        sampleDataset.setCreatedBy("testuser");
        sampleDataset.getTags().add(sampleTag);
    }

    @Test
    @DisplayName("datasetsGet: 正常分页查询数据集")
    void getDatasets_success() {
        // Given
        List<Dataset> datasets = Collections.singletonList(sampleDataset);
        Page<Dataset> page = new PageImpl<>(datasets, PageRequest.of(0, 20), 1);
        when(datasetApplicationService.getDatasets(any())).thenReturn(page);

        // When
        ResponseEntity<Response<PagedResponse<DatasetResponse>>> response = controller.getDatasets(new DatasetPagingQuery("CSV",
                "tag1,tag2", "test", "ACTIVE"));

        // Then
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(1, response.getBody().getData().getContent().size());
        assertEquals(0, response.getBody().getData().getPage());
        assertEquals(20, response.getBody().getData().getSize());
        assertEquals(1, response.getBody().getData().getTotalElements());
        assertEquals(1, response.getBody().getData().getTotalPages());

        DatasetResponse datasetResponse = response.getBody().getData().getContent().getFirst();
        assertEquals("dataset-id-1", datasetResponse.getId());
        assertEquals("Test Dataset", datasetResponse.getName());
        assertEquals("CSV", datasetResponse.getDatasetType());
        assertEquals(1, datasetResponse.getTags().size());
        assertEquals("test-tag", datasetResponse.getTags().getFirst().getName());

        verify(datasetApplicationService).getDatasets(any());
    }

    @Test
    @DisplayName("datasetsGet: 默认分页参数")
    void getDatasets_defaultPaging() {
        Page<Dataset> emptyPage = new PageImpl<>(Collections.emptyList(), PageRequest.of(0, 20), 0);
        when(datasetApplicationService.getDatasets(any()))
                .thenReturn(emptyPage);

        ResponseEntity<Response<PagedResponse<DatasetResponse>>> response = controller.getDatasets(new DatasetPagingQuery());

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertTrue(response.getBody().getData().getContent().isEmpty());
        verify(datasetApplicationService).getDatasets(argThat(pageable -> pageable.getPage() == 0 && pageable.getSize() == 20));
    }

    @Test
    @DisplayName("datasetsGet: 标签参数解析")
    void getDatasets_tagsProcessing() {
        Page<Dataset> page = new PageImpl<>(Collections.emptyList(), PageRequest.of(0, 20), 0);
        when(datasetApplicationService.getDatasets(any()))
                .thenReturn(page);

        // 测试空标签
        controller.getDatasets(new DatasetPagingQuery(null, "", null, null));
        verify(datasetApplicationService).getDatasets(any());

        // 测试空白标签
        controller.getDatasets(new DatasetPagingQuery(null, "   ", null, null));
        verify(datasetApplicationService, times(2)).getDatasets(any());
    }

    @Test
    @DisplayName("datasetsPost: 正常创建数据集")
    void createDataset_success() {
        CreateDatasetRequest request = new CreateDatasetRequest();
        request.setName("New Dataset");
        request.setDescription("New description");
        request.setDatasetType("JSON");
        request.setTags(Arrays.asList("tag1", "tag2"));
        request.setDataSource("123");
        request.setTargetLocation("/new/path");

        when(datasetApplicationService.createDataset(any())).thenReturn(sampleDataset);

        ResponseEntity<Response<DatasetResponse>> response = controller.createDataset(request);

        assertEquals(HttpStatus.CREATED, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("dataset-id-1", response.getBody().getData().getId());
        verify(datasetApplicationService).createDataset(any());
    }

    @Test
    @DisplayName("datasetsPost: 数据源ID转换异常时传入null")
    void createDataset_invalidDataSourceId() {
        CreateDatasetRequest request = new CreateDatasetRequest();
        request.setName("New Dataset");
        request.setDataSource("invalid-id");

        when(datasetApplicationService.createDataset(any()))
                .thenReturn(sampleDataset);

        ResponseEntity<Response<DatasetResponse>> response = controller.createDataset(request);

        assertEquals(HttpStatus.CREATED, response.getStatusCode());
        verify(datasetApplicationService).createDataset(any());
    }

    @Test
    @DisplayName("datasetsPost: 服务抛异常时返回400")
    void createDataset_serviceException() {
        CreateDatasetRequest request = new CreateDatasetRequest();
        request.setName("Duplicate Dataset");

        when(datasetApplicationService.createDataset(any())).thenThrow(new IllegalArgumentException("Already exists"));

        ResponseEntity<Response<DatasetResponse>> response = controller.createDataset(request);

        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        assertNull(response.getBody());
    }

    @Test
    @DisplayName("datasetsDatasetIdGet: 正常获取数据集详情")
    void getDatasetById_success() {
        when(datasetApplicationService.getDataset("dataset-id-1")).thenReturn(sampleDataset);

        ResponseEntity<Response<DatasetResponse>> response = controller.getDatasetById("dataset-id-1");

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("dataset-id-1", response.getBody().getData().getId());
        assertEquals("Test Dataset", response.getBody().getData().getName());
        assertEquals("1", response.getBody().getData().getDataSource());
        assertEquals("/test/path", response.getBody().getData().getTargetLocation());
        assertEquals(10, response.getBody().getData().getFileCount());
        assertEquals(1024L, response.getBody().getData().getTotalSize());
        assertEquals(80.0f, response.getBody().getData().getCompletionRate());
        assertEquals("testuser", response.getBody().getData().getCreatedBy());

        verify(datasetApplicationService).getDataset("dataset-id-1");
    }

    @Test
    @DisplayName("datasetsDatasetIdGet: 数据集不存在时返回404")
    void getDatasetById_notFound() {
        when(datasetApplicationService.getDataset("not-exist"))
                .thenThrow(new IllegalArgumentException("Dataset not found"));

        ResponseEntity<Response<DatasetResponse>> response = controller.getDatasetById("not-exist");

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
        assertNull(response.getBody());
    }


    @Test
    @DisplayName("datasetsDatasetIdPut: 状态为null时传入null")
    void updateDataset_nullStatus() {
        UpdateDatasetRequest request = new UpdateDatasetRequest();
        request.setName("Updated Name");
        request.setStatus(null);

        when(datasetApplicationService.updateDataset(eq("dataset-id-1"), eq("Updated Name"),
                isNull(), isNull(), isNull())).thenReturn(sampleDataset);

        ResponseEntity<Response<DatasetResponse>> response = controller.updateDataset("dataset-id-1", request);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        verify(datasetApplicationService).updateDataset(eq("dataset-id-1"), eq("Updated Name"),
                isNull(), isNull(), isNull());
    }

    @Test
    @DisplayName("datasetsDatasetIdPut: 数据集不存在时返回404")
    void updateDataset_notFound() {
        UpdateDatasetRequest request = new UpdateDatasetRequest();
        request.setName("Updated Name");

        when(datasetApplicationService.updateDataset(anyString(), anyString(), any(), any(), any()))
                .thenThrow(new IllegalArgumentException("Dataset not found"));

        ResponseEntity<Response<DatasetResponse>> response = controller.updateDataset("not-exist", request);

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
        assertNull(response.getBody());
    }

    @Test
    @DisplayName("datasetsDatasetIdDelete: 正常删除数据集")
    void deleteDataset_success() {
        doNothing().when(datasetApplicationService).deleteDataset("dataset-id-1");

        ResponseEntity<Response<Void>> response = controller.deleteDataset("dataset-id-1");

        assertEquals(HttpStatus.NO_CONTENT, response.getStatusCode());
        verify(datasetApplicationService).deleteDataset("dataset-id-1");
    }

    @Test
    @DisplayName("datasetsDatasetIdDelete: 数据集不存在时返回404")
    void deleteDataset_notFound() {
        doThrow(new IllegalArgumentException("Dataset not found"))
                .when(datasetApplicationService).deleteDataset("not-exist");

        ResponseEntity<Response<Void>> response = controller.deleteDataset("not-exist");

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
    }

    @Test
    @DisplayName("datasetsDatasetIdStatisticsGet: 正常获取统计信息")
    void getDatasetStatistics_success() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("totalFiles", 100);
        stats.put("completedFiles", 80);
        stats.put("totalSize", 2048L);
        stats.put("completionRate", 80.0f);
        stats.put("fileTypeDistribution", Map.of("csv", 60, "json", 40));
        stats.put("statusDistribution", Map.of("COMPLETED", 80, "PROCESSING", 20));

        when(datasetApplicationService.getDatasetStatistics("dataset-id-1")).thenReturn(stats);

        ResponseEntity<Response<DatasetStatisticsResponse>> response = controller.getDatasetStatistics("dataset-id-1");

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(100, response.getBody().getData().getTotalFiles());
        assertEquals(80, response.getBody().getData().getCompletedFiles());
        assertEquals(2048L, response.getBody().getData().getTotalSize());
        assertEquals(80.0f, response.getBody().getData().getCompletionRate());
        assertNotNull(response.getBody().getData().getFileTypeDistribution());
        assertNotNull(response.getBody().getData().getStatusDistribution());

        verify(datasetApplicationService).getDatasetStatistics("dataset-id-1");
    }

    @Test
    @DisplayName("datasetsDatasetIdStatisticsGet: 数据集不存在时返回404")
    void getDatasetStatistics_notFound() {
        when(datasetApplicationService.getDatasetStatistics("not-exist"))
                .thenThrow(new IllegalArgumentException("Dataset not found"));

        ResponseEntity<Response<DatasetStatisticsResponse>> response = controller.getDatasetStatistics("not-exist");

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
        assertNull(response.getBody());
    }

    @Test
    @DisplayName("datasetsDatasetIdStatisticsGet: 其他异常时返回500")
    void getDatasetStatistics_internalError() {
        when(datasetApplicationService.getDatasetStatistics("dataset-id-1"))
                .thenThrow(new RuntimeException("Internal error"));

        ResponseEntity<Response<DatasetStatisticsResponse>> response = controller.getDatasetStatistics("dataset-id-1");

        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
        assertNull(response.getBody());
    }

}
