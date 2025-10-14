package com.dataengine.datamanagement.application.service;

import com.dataengine.common.domain.service.FileService;
import com.dataengine.datamanagement.domain.model.dataset.Dataset;
import com.dataengine.datamanagement.domain.model.dataset.DatasetFile;
import com.dataengine.datamanagement.domain.model.dataset.StatusConstants;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.DatasetFileMapper;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.DatasetMapper;
import org.apache.ibatis.session.RowBounds;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.core.io.Resource;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class DatasetFileApplicationServiceTest {

    @Mock
    private DatasetFileMapper datasetFileMapper;

    @Mock
    private DatasetMapper datasetMapper;

    @Mock
    private MultipartFile multipartFile;

    @Mock
    private FileService fileService;

    private DatasetFileApplicationService service;
    private Dataset sampleDataset;
    private DatasetFile sampleFile;

    @BeforeEach
    void setUp() {
        // 使用临时目录进行测试
        String tempDir = System.getProperty("java.io.tmpdir") + "/test-uploads";
        service = new DatasetFileApplicationService(datasetFileMapper, datasetMapper, fileService, tempDir);

        sampleDataset = new Dataset();
        sampleDataset.setId("dataset-id-1");
        sampleDataset.setName("Test Dataset");
        sampleDataset.setFileCount(5L);
        sampleDataset.setSizeBytes(1024L);

        sampleFile = new DatasetFile();
        sampleFile.setId("file-id-1");
        sampleFile.setDatasetId("dataset-id-1");
        sampleFile.setFileName("test.csv");
        sampleFile.setFilePath("/path/to/test.csv");
        sampleFile.setFileSize(512L);
        sampleFile.setFileType("text/csv");
        sampleFile.setStatus(StatusConstants.DatasetFileStatuses.COMPLETED);
        sampleFile.setUploadTime(LocalDateTime.now());
    }

    @Test
    @DisplayName("uploadFile: 正常上传文件")
    void uploadFile_success() throws IOException {
        // Given
        when(datasetMapper.findById("dataset-id-1")).thenReturn(sampleDataset);
        when(multipartFile.getOriginalFilename()).thenReturn("test.csv");
        when(multipartFile.getContentType()).thenReturn("text/csv");
        when(multipartFile.getSize()).thenReturn(1024L);
        when(multipartFile.getInputStream()).thenReturn(mock(InputStream.class));
        when(datasetFileMapper.insert(any(DatasetFile.class))).thenReturn(1);
        when(datasetFileMapper.findByDatasetIdAndFileName(eq("dataset-id-1"), anyString())).thenReturn(sampleFile);
        when(datasetMapper.update(any(Dataset.class))).thenReturn(1);

        // When
        DatasetFile result = service.uploadFile("dataset-id-1", multipartFile, "Test description", "user1");

        // Then
        assertNotNull(result);
        verify(datasetMapper).findById("dataset-id-1");

        ArgumentCaptor<DatasetFile> fileCaptor = ArgumentCaptor.forClass(DatasetFile.class);
        verify(datasetFileMapper).insert(fileCaptor.capture());
        DatasetFile insertedFile = fileCaptor.getValue();
        assertNotNull(insertedFile.getId());
        assertEquals("dataset-id-1", insertedFile.getDatasetId());
        assertTrue(insertedFile.getFileName().contains("test.csv"));
        assertEquals("text/csv", insertedFile.getFileType());
        assertEquals("csv", insertedFile.getFileFormat());
        assertEquals(1024L, insertedFile.getFileSize());
        assertEquals(StatusConstants.DatasetFileStatuses.COMPLETED, insertedFile.getStatus());

        verify(datasetMapper).update(any(Dataset.class));
        verify(datasetFileMapper).findByDatasetIdAndFileName(eq("dataset-id-1"), anyString());
    }

    @Test
    @DisplayName("uploadFile: 数据集不存在时抛异常")
    void uploadFile_datasetNotFound() {
        when(datasetMapper.findById("not-exist")).thenReturn(null);

        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                () -> service.uploadFile("not-exist", multipartFile, "desc", "user1"));

        assertTrue(ex.getMessage().contains("Dataset not found"));
        verify(datasetMapper).findById("not-exist");
        verify(datasetFileMapper, never()).insert(any());
    }

    @Test
    @DisplayName("uploadFile: 文件名为null时使用默认名称")
    void uploadFile_nullFileName() throws IOException {
        when(datasetMapper.findById("dataset-id-1")).thenReturn(sampleDataset);
        when(multipartFile.getOriginalFilename()).thenReturn(null);
        when(multipartFile.getContentType()).thenReturn("text/plain");
        when(multipartFile.getSize()).thenReturn(512L);
        when(multipartFile.getInputStream()).thenReturn(mock(InputStream.class));
        when(datasetFileMapper.insert(any(DatasetFile.class))).thenReturn(1);
        when(datasetFileMapper.findByDatasetIdAndFileName(eq("dataset-id-1"), anyString())).thenReturn(sampleFile);
        when(datasetMapper.update(any(Dataset.class))).thenReturn(1);

        DatasetFile result = service.uploadFile("dataset-id-1", multipartFile, "desc", "user1");

        assertNotNull(result);
        ArgumentCaptor<DatasetFile> captor = ArgumentCaptor.forClass(DatasetFile.class);
        verify(datasetFileMapper).insert(captor.capture());
        DatasetFile inserted = captor.getValue();
        assertTrue(inserted.getFileName().contains("file"));
    }

    @Test
    @DisplayName("uploadFile: IOException时抛RuntimeException")
    void uploadFile_ioException() throws IOException {
        when(datasetMapper.findById("dataset-id-1")).thenReturn(sampleDataset);
        when(multipartFile.getOriginalFilename()).thenReturn("test.txt");
        when(multipartFile.getInputStream()).thenThrow(new IOException("IO error"));

        RuntimeException ex = assertThrows(RuntimeException.class,
                () -> service.uploadFile("dataset-id-1", multipartFile, "desc", "user1"));

        assertTrue(ex.getMessage().contains("Could not store file"));
        verify(datasetFileMapper, never()).insert(any());
    }

    @Test
    @DisplayName("getDatasetFiles: 分页查询文件列表")
    void getDatasetFiles_pagination() {
        List<DatasetFile> files = Arrays.asList(sampleFile);
        Pageable pageable = PageRequest.of(0, 10);

        when(datasetFileMapper.findByCriteria(eq("dataset-id-1"), eq("text/csv"),
                eq(StatusConstants.DatasetFileStatuses.COMPLETED), any(RowBounds.class))).thenReturn(files);

        Page<DatasetFile> result = service.getDatasetFiles("dataset-id-1", "text/csv",
                StatusConstants.DatasetFileStatuses.COMPLETED, pageable);

        assertNotNull(result);
        assertEquals(1, result.getContent().size());
        verify(datasetFileMapper).findByCriteria(eq("dataset-id-1"), eq("text/csv"),
                eq(StatusConstants.DatasetFileStatuses.COMPLETED), any(RowBounds.class));
    }

    @Test
    @DisplayName("getDatasetFiles: 空结果集")
    void getDatasetFiles_emptyResult() {
        Pageable pageable = PageRequest.of(0, 10);
        when(datasetFileMapper.findByCriteria(eq("dataset-id-1"), isNull(),
                isNull(), any(RowBounds.class))).thenReturn(Collections.emptyList());

        Page<DatasetFile> result = service.getDatasetFiles("dataset-id-1", null, null, pageable);

        assertNotNull(result);
        assertTrue(result.getContent().isEmpty());
    }

    @Test
    @DisplayName("getDatasetFile: 正常获取文件详情")
    void getDatasetFile_success() {
        when(datasetFileMapper.findById("file-id-1")).thenReturn(sampleFile);

        DatasetFile result = service.getDatasetFile("dataset-id-1", "file-id-1");

        assertNotNull(result);
        assertSame(sampleFile, result);
        verify(datasetFileMapper).findById("file-id-1");
    }

    @Test
    @DisplayName("getDatasetFile: 文件不存在时抛异常")
    void getDatasetFile_notFound() {
        when(datasetFileMapper.findById("not-exist")).thenReturn(null);

        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                () -> service.getDatasetFile("dataset-id-1", "not-exist"));

        assertTrue(ex.getMessage().contains("File not found"));
        verify(datasetFileMapper).findById("not-exist");
    }

    @Test
    @DisplayName("getDatasetFile: 文件不属于指定数据集时抛异常")
    void getDatasetFile_wrongDataset() {
        DatasetFile wrongFile = new DatasetFile();
        wrongFile.setDatasetId("other-dataset");
        when(datasetFileMapper.findById("file-id-1")).thenReturn(wrongFile);

        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                () -> service.getDatasetFile("dataset-id-1", "file-id-1"));

        assertTrue(ex.getMessage().contains("does not belong to the specified dataset"));
        verify(datasetFileMapper).findById("file-id-1");
    }

    @Test
    @DisplayName("deleteDatasetFile: 正常删除文件")
    void deleteDatasetFile_success() {
        when(datasetFileMapper.findById("file-id-1")).thenReturn(sampleFile);
        when(datasetFileMapper.deleteById("file-id-1")).thenReturn(1);
        when(datasetMapper.findById("dataset-id-1")).thenReturn(sampleDataset);
        when(datasetMapper.update(any(Dataset.class))).thenReturn(1);

        assertDoesNotThrow(() -> service.deleteDatasetFile("dataset-id-1", "file-id-1"));

        verify(datasetFileMapper).findById("file-id-1");
        verify(datasetFileMapper).deleteById("file-id-1");
        verify(datasetMapper).findById("dataset-id-1");

        ArgumentCaptor<Dataset> captor = ArgumentCaptor.forClass(Dataset.class);
        verify(datasetMapper).update(captor.capture());
        Dataset updated = captor.getValue();
        assertEquals(4L, updated.getFileCount()); // 原来5个，删除1个
        assertEquals(512L, updated.getSizeBytes()); // 原来1024，减去512
    }

    @Test
    @DisplayName("deleteDatasetFile: 文件不存在时抛异常")
    void deleteDatasetFile_notFound() {
        when(datasetFileMapper.findById("not-exist")).thenReturn(null);

        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                () -> service.deleteDatasetFile("dataset-id-1", "not-exist"));

        assertTrue(ex.getMessage().contains("File not found"));
        verify(datasetFileMapper).findById("not-exist");
        verify(datasetFileMapper, never()).deleteById(anyString());
    }

    @Test
    @DisplayName("deleteDatasetFile: 统计数据不能为负数")
    void deleteDatasetFile_negativeStats() {
        Dataset smallDataset = new Dataset();
        smallDataset.setFileCount(0L);
        smallDataset.setSizeBytes(0L);

        when(datasetFileMapper.findById("file-id-1")).thenReturn(sampleFile);
        when(datasetFileMapper.deleteById("file-id-1")).thenReturn(1);
        when(datasetMapper.findById("dataset-id-1")).thenReturn(smallDataset);
        when(datasetMapper.update(any(Dataset.class))).thenReturn(1);

        service.deleteDatasetFile("dataset-id-1", "file-id-1");

        ArgumentCaptor<Dataset> captor = ArgumentCaptor.forClass(Dataset.class);
        verify(datasetMapper).update(captor.capture());
        Dataset updated = captor.getValue();
        assertEquals(0L, updated.getFileCount());
        assertEquals(0L, updated.getSizeBytes());
    }

    @Test
    @DisplayName("downloadFile: 正常下载文件")
    void downloadFile_success() throws Exception {
        // 创建临时文件用于测试
        Path tempFile = Files.createTempFile("test", ".csv");
        Files.write(tempFile, "test content".getBytes());

        sampleFile.setFilePath(tempFile.toString());
        when(datasetFileMapper.findById("file-id-1")).thenReturn(sampleFile);

        Resource result = service.downloadFile("dataset-id-1", "file-id-1");

        assertNotNull(result);
        assertTrue(result.exists());
        verify(datasetFileMapper).findById("file-id-1");

        // 清理临时文件
        Files.deleteIfExists(tempFile);
    }

    @Test
    @DisplayName("downloadFile: 文件不存在时抛RuntimeException")
    void downloadFile_fileNotExist() {
        sampleFile.setFilePath("/non/existent/path");
        when(datasetFileMapper.findById("file-id-1")).thenReturn(sampleFile);

        RuntimeException ex = assertThrows(RuntimeException.class,
                () -> service.downloadFile("dataset-id-1", "file-id-1"));

        assertTrue(ex.getMessage().contains("File not found"));
        verify(datasetFileMapper).findById("file-id-1");
    }

    @Test
    @DisplayName("downloadFile: 文件记录不存在时抛异常")
    void downloadFile_recordNotFound() {
        when(datasetFileMapper.findById("not-exist")).thenReturn(null);

        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                () -> service.downloadFile("dataset-id-1", "not-exist"));

        assertTrue(ex.getMessage().contains("File not found"));
        verify(datasetFileMapper).findById("not-exist");
    }

    @Test
    @DisplayName("getFileExtension: 测试文件扩展名提取")
    void testFileExtensionExtraction() throws Exception {
        // 通过uploadFile间接测试getFileExtension方法
        when(datasetMapper.findById("dataset-id-1")).thenReturn(sampleDataset);
        when(multipartFile.getOriginalFilename()).thenReturn("document.pdf");
        when(multipartFile.getContentType()).thenReturn("application/pdf");
        when(multipartFile.getSize()).thenReturn(1024L);
        when(multipartFile.getInputStream()).thenReturn(mock(InputStream.class));
        when(datasetFileMapper.insert(any(DatasetFile.class))).thenReturn(1);
        when(datasetFileMapper.findByDatasetIdAndFileName(eq("dataset-id-1"), anyString())).thenReturn(sampleFile);
        when(datasetMapper.update(any(Dataset.class))).thenReturn(1);

        service.uploadFile("dataset-id-1", multipartFile, "desc", "user1");

        ArgumentCaptor<DatasetFile> captor = ArgumentCaptor.forClass(DatasetFile.class);
        verify(datasetFileMapper).insert(captor.capture());
        DatasetFile inserted = captor.getValue();
        assertEquals("pdf", inserted.getFileFormat());
    }

    @Test
    @DisplayName("getFileExtension: 无扩展名文件")
    void testFileWithoutExtension() throws Exception {
        when(datasetMapper.findById("dataset-id-1")).thenReturn(sampleDataset);
        when(multipartFile.getOriginalFilename()).thenReturn("README");
        when(multipartFile.getContentType()).thenReturn("text/plain");
        when(multipartFile.getSize()).thenReturn(1024L);
        when(multipartFile.getInputStream()).thenReturn(mock(InputStream.class));
        when(datasetFileMapper.insert(any(DatasetFile.class))).thenReturn(1);
        when(datasetFileMapper.findByDatasetIdAndFileName(eq("dataset-id-1"), anyString())).thenReturn(sampleFile);
        when(datasetMapper.update(any(Dataset.class))).thenReturn(1);

        service.uploadFile("dataset-id-1", multipartFile, "desc", "user1");

        ArgumentCaptor<DatasetFile> captor = ArgumentCaptor.forClass(DatasetFile.class);
        verify(datasetFileMapper).insert(captor.capture());
        DatasetFile inserted = captor.getValue();
        assertNull(inserted.getFileFormat());
    }
}
