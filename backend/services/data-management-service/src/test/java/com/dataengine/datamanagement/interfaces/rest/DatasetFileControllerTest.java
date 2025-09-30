package com.dataengine.datamanagement.interfaces.rest;

import com.dataengine.datamanagement.application.service.DatasetFileApplicationService;
import com.dataengine.datamanagement.domain.model.dataset.DatasetFile;
import com.dataengine.datamanagement.domain.model.dataset.StatusConstants;
import com.dataengine.datamanagement.interfaces.dto.DatasetFileResponse;
import com.dataengine.datamanagement.interfaces.dto.PagedDatasetFileResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class DatasetFileControllerTest {

    @Mock
    private DatasetFileApplicationService datasetFileApplicationService;

    @Mock
    private MultipartFile multipartFile;

    @InjectMocks
    private DatasetFileController controller;

    private DatasetFile sampleFile;

    @BeforeEach
    void setUp() {
        sampleFile = new DatasetFile();
        sampleFile.setId("file-id-1");
        sampleFile.setDatasetId("dataset-id-1");
        sampleFile.setFileName("test-file.csv");
        sampleFile.setFileType("text/csv");
        sampleFile.setFileSize(1024L);
        sampleFile.setStatus(StatusConstants.DatasetFileStatuses.COMPLETED);
        sampleFile.setFilePath("/path/to/test-file.csv");
        sampleFile.setUploadTime(LocalDateTime.now());
    }

    @Test
    @DisplayName("datasetsDatasetIdFilesGet: 正常分页查询文件列表")
    void getDatasetFiles_success() {
        // Given
        List<DatasetFile> files = Arrays.asList(sampleFile);
        Page<DatasetFile> page = new PageImpl<>(files, PageRequest.of(0, 20), 1);
        when(datasetFileApplicationService.getDatasetFiles(eq("dataset-id-1"), eq("text/csv"),
                eq(StatusConstants.DatasetFileStatuses.COMPLETED), any())).thenReturn(page);

        // When
        ResponseEntity<PagedDatasetFileResponse> response = controller.getDatasetFiles(
                "dataset-id-1", 0, 20, "text/csv", StatusConstants.DatasetFileStatuses.COMPLETED);

        // Then
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(1, response.getBody().getContent().size());
        assertEquals(0, response.getBody().getPage());
        assertEquals(20, response.getBody().getSize());
        assertEquals(1, response.getBody().getTotalElements());
        assertEquals(1, response.getBody().getTotalPages());
        assertTrue(response.getBody().getFirst());
        assertTrue(response.getBody().getLast());

        DatasetFileResponse fileResponse = response.getBody().getContent().get(0);
        assertEquals("file-id-1", fileResponse.getId());
        assertEquals("test-file.csv", fileResponse.getFileName());
        assertEquals("text/csv", fileResponse.getFileType());
        assertEquals(1024L, fileResponse.getSize());
        assertEquals("/path/to/test-file.csv", fileResponse.getFilePath());

        verify(datasetFileApplicationService).getDatasetFiles(eq("dataset-id-1"), eq("text/csv"),
                eq(StatusConstants.DatasetFileStatuses.COMPLETED), any());
    }

    @Test
    @DisplayName("datasetsDatasetIdFilesGet: 默认分页参数")
    void getDatasetFiles_defaultPaging() {
        Page<DatasetFile> emptyPage = new PageImpl<>(Collections.emptyList(), PageRequest.of(0, 20), 0);
        when(datasetFileApplicationService.getDatasetFiles(eq("dataset-id-1"), isNull(), isNull(), any()))
                .thenReturn(emptyPage);

        ResponseEntity<PagedDatasetFileResponse> response = controller.getDatasetFiles(
                "dataset-id-1", null, null, null, null);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertTrue(response.getBody().getContent().isEmpty());
        verify(datasetFileApplicationService).getDatasetFiles(eq("dataset-id-1"), isNull(), isNull(),
                argThat(pageable -> pageable.getPageNumber() == 0 && pageable.getPageSize() == 20));
    }

    @Test
    @DisplayName("datasetsDatasetIdFilesGet: 空结果集")
    void getDatasetFiles_emptyResult() {
        Page<DatasetFile> emptyPage = new PageImpl<>(Collections.emptyList(), PageRequest.of(0, 10), 0);
        when(datasetFileApplicationService.getDatasetFiles(eq("dataset-id-1"), isNull(), isNull(), any()))
                .thenReturn(emptyPage);

        ResponseEntity<PagedDatasetFileResponse> response = controller.getDatasetFiles(
                "dataset-id-1", 0, 10, null, null);

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertTrue(response.getBody().getContent().isEmpty());
        assertEquals(0, response.getBody().getTotalElements());
    }

    @Test
    @DisplayName("datasetsDatasetIdFilesPost: 正常上传文件")
    void uploadDatasetFile_success() {
        when(datasetFileApplicationService.uploadFile(eq("dataset-id-1"), eq(multipartFile),
                eq("Test description"), eq("system"))).thenReturn(sampleFile);

        ResponseEntity<DatasetFileResponse> response = controller.uploadDatasetFile(
                "dataset-id-1", multipartFile, "Test description");

        assertEquals(HttpStatus.CREATED, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("file-id-1", response.getBody().getId());
        assertEquals("test-file.csv", response.getBody().getFileName());
        assertEquals("text/csv", response.getBody().getFileType());
        assertEquals(1024L, response.getBody().getSize());

        verify(datasetFileApplicationService).uploadFile(eq("dataset-id-1"), eq(multipartFile),
                eq("Test description"), eq("system"));
    }

    @Test
    @DisplayName("datasetsDatasetIdFilesPost: 非法参数时返回400")
    void uploadDatasetFile_badRequest() {
        when(datasetFileApplicationService.uploadFile(eq("dataset-id-1"), eq(multipartFile),
                any(), eq("system"))).thenThrow(new IllegalArgumentException("Dataset not found"));

        ResponseEntity<DatasetFileResponse> response = controller.uploadDatasetFile(
                "dataset-id-1", multipartFile, "desc");

        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        assertNull(response.getBody());
    }

    @Test
    @DisplayName("datasetsDatasetIdFilesPost: 运行时异常时返回500")
    void uploadDatasetFile_internalError() {
        when(datasetFileApplicationService.uploadFile(eq("dataset-id-1"), eq(multipartFile),
                any(), eq("system"))).thenThrow(new RuntimeException("IO error"));

        ResponseEntity<DatasetFileResponse> response = controller.uploadDatasetFile(
                "dataset-id-1", multipartFile, "desc");

        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
        assertNull(response.getBody());
    }

    @Test
    @DisplayName("datasetsDatasetIdFilesFileIdGet: 正常获取文件详情")
    void getDatasetFileById_success() {
        when(datasetFileApplicationService.getDatasetFile("dataset-id-1", "file-id-1"))
                .thenReturn(sampleFile);

        ResponseEntity<DatasetFileResponse> response = controller.getDatasetFileById(
                "dataset-id-1", "file-id-1");

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("file-id-1", response.getBody().getId());
        assertEquals("test-file.csv", response.getBody().getFileName());
        assertEquals("text/csv", response.getBody().getFileType());

        verify(datasetFileApplicationService).getDatasetFile("dataset-id-1", "file-id-1");
    }

    @Test
    @DisplayName("datasetsDatasetIdFilesFileIdGet: 文件不存在时返回404")
    void getDatasetFileById_notFound() {
        when(datasetFileApplicationService.getDatasetFile("dataset-id-1", "not-exist"))
                .thenThrow(new IllegalArgumentException("File not found"));

        ResponseEntity<DatasetFileResponse> response = controller.getDatasetFileById(
                "dataset-id-1", "not-exist");

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
        assertNull(response.getBody());
    }

    @Test
    @DisplayName("datasetsDatasetIdFilesFileIdDelete: 正常删除文件")
    void deleteDatasetFile_success() {
        doNothing().when(datasetFileApplicationService).deleteDatasetFile("dataset-id-1", "file-id-1");

        ResponseEntity<Void> response = controller.deleteDatasetFile(
                "dataset-id-1", "file-id-1");

        assertEquals(HttpStatus.NO_CONTENT, response.getStatusCode());
        verify(datasetFileApplicationService).deleteDatasetFile("dataset-id-1", "file-id-1");
    }

    @Test
    @DisplayName("datasetsDatasetIdFilesFileIdDelete: 文件不存在时返回404")
    void deleteDatasetFile_notFound() {
        doThrow(new IllegalArgumentException("File not found"))
                .when(datasetFileApplicationService).deleteDatasetFile("dataset-id-1", "not-exist");

        ResponseEntity<Void> response = controller.deleteDatasetFile(
                "dataset-id-1", "not-exist");

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
    }

    @Test
    @DisplayName("datasetsDatasetIdFilesFileIdDownloadGet: 正常下载文件")
    void downloadDatasetFile_success() {
        Resource resource = new ByteArrayResource("file content".getBytes());
        when(datasetFileApplicationService.getDatasetFile("dataset-id-1", "file-id-1"))
                .thenReturn(sampleFile);
        when(datasetFileApplicationService.downloadFile("dataset-id-1", "file-id-1"))
                .thenReturn(resource);

        ResponseEntity<Resource> response = controller.downloadDatasetFile(
                "dataset-id-1", "file-id-1");

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(MediaType.APPLICATION_OCTET_STREAM, response.getHeaders().getContentType());
        assertTrue(response.getHeaders().get(HttpHeaders.CONTENT_DISPOSITION)
                .toString().contains("test-file.csv"));

        verify(datasetFileApplicationService).getDatasetFile("dataset-id-1", "file-id-1");
        verify(datasetFileApplicationService).downloadFile("dataset-id-1", "file-id-1");
    }

    @Test
    @DisplayName("datasetsDatasetIdFilesFileIdDownloadGet: 文件不存在时返回404")
    void downloadDatasetIdFilesFileIdDownloadGet_fileNotFound() {
        when(datasetFileApplicationService.getDatasetFile("dataset-id-1", "not-exist"))
                .thenThrow(new IllegalArgumentException("File not found"));

        ResponseEntity<Resource> response = controller.downloadDatasetFile(
                "dataset-id-1", "not-exist");

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
        assertNull(response.getBody());
    }

    @Test
    @DisplayName("datasetsDatasetIdFilesFileIdDownloadGet: 下载异常时返回500")
    void downloadDatasetFileIdDownloadGet_downloadError() {
        when(datasetFileApplicationService.getDatasetFile("dataset-id-1", "file-id-1"))
                .thenReturn(sampleFile);
        when(datasetFileApplicationService.downloadFile("dataset-id-1", "file-id-1"))
                .thenThrow(new RuntimeException("Download error"));

        ResponseEntity<Resource> response = controller.downloadDatasetFile(
                "dataset-id-1", "file-id-1");

        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
        assertNull(response.getBody());
    }

    @Test
    @DisplayName("convertToResponse: 正常转换文件响应")
    void convertToResponse_success() {
        // 通过public API间接测试convertToResponse方法
        when(datasetFileApplicationService.getDatasetFile("dataset-id-1", "file-id-1"))
                .thenReturn(sampleFile);

        ResponseEntity<DatasetFileResponse> response = controller.getDatasetFileById(
                "dataset-id-1", "file-id-1");

        DatasetFileResponse fileResponse = response.getBody();
        assertNotNull(fileResponse);
        assertEquals("file-id-1", fileResponse.getId());
        assertEquals("test-file.csv", fileResponse.getFileName());
        assertNull(fileResponse.getOriginalName());
        assertEquals("text/csv", fileResponse.getFileType());
        assertEquals(1024L, fileResponse.getSize());
        assertNotNull(fileResponse.getStatus());
        assertNull(fileResponse.getDescription());
        assertEquals("/path/to/test-file.csv", fileResponse.getFilePath());
        assertNotNull(fileResponse.getUploadedAt());
        assertNull(fileResponse.getUploadedBy());
    }

    @Test
    @DisplayName("convertToResponse: 处理null值")
    void convertToResponse_nullValues() {
        DatasetFile minimalFile = new DatasetFile();
        minimalFile.setId("minimal-file");
        minimalFile.setFileName("minimal.txt");

        when(datasetFileApplicationService.getDatasetFile("dataset-id-1", "minimal-file"))
                .thenReturn(minimalFile);

        ResponseEntity<DatasetFileResponse> response = controller.getDatasetFileById(
                "dataset-id-1", "minimal-file");

        DatasetFileResponse fileResponse = response.getBody();
        assertNotNull(fileResponse);
        assertEquals("minimal-file", fileResponse.getId());
        assertEquals("minimal.txt", fileResponse.getFileName());
        assertNull(fileResponse.getFileType());
        assertNull(fileResponse.getSize());
        assertNull(fileResponse.getFilePath());
        assertNull(fileResponse.getUploadedAt());
    }

    @Test
    @DisplayName("convertToResponse: 状态转换异常时忽略")
    void convertToResponse_statusConversionError() {
        DatasetFile fileWithInvalidStatus = new DatasetFile();
        fileWithInvalidStatus.setId("invalid-status-file");
        fileWithInvalidStatus.setFileName("test.txt");
        fileWithInvalidStatus.setStatus("INVALID_STATUS");

        when(datasetFileApplicationService.getDatasetFile("dataset-id-1", "invalid-status-file"))
                .thenReturn(fileWithInvalidStatus);

        ResponseEntity<DatasetFileResponse> response = controller.getDatasetFileById(
                "dataset-id-1", "invalid-status-file");

        DatasetFileResponse fileResponse = response.getBody();
        assertNotNull(fileResponse);
        assertEquals("invalid-status-file", fileResponse.getId());
        // 状态转换失败时应该不设置或设置为null
    }
}
