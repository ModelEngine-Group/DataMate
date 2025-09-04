package com.dataengine.datamanagement.domain.model.dataset;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;

import static org.junit.jupiter.api.Assertions.*;

class DatasetFileTest {

    private DatasetFile datasetFile;

    @BeforeEach
    void setUp() {
        datasetFile = new DatasetFile();
    }

    @Test
    @DisplayName("constructor: 默认构造函数")
    void testDefaultConstructor() {
        DatasetFile file = new DatasetFile();
        
        assertNull(file.getId());
        assertNull(file.getDatasetId());
        assertNull(file.getFileName());
        assertNull(file.getFilePath());
        assertNull(file.getFileType());
        assertNull(file.getFileSize());
        assertNull(file.getFileFormat());
        assertNull(file.getUploadTime());
        assertNull(file.getLastAccessTime());
        assertNull(file.getStatus());
    }

    @Test
    @DisplayName("constructor: 参数构造函数")
    void testParameterizedConstructor() {
        String datasetId = "dataset-123";
        String fileName = "test.csv";
        String filePath = "/path/to/test.csv";
        String fileType = "TEXT";
        Long fileSize = 1024L;
        String fileFormat = "csv";

        DatasetFile file = new DatasetFile(datasetId, fileName, filePath, fileType, fileSize, fileFormat);

        assertNull(file.getId()); // ID需要单独设置
        assertEquals(datasetId, file.getDatasetId());
        assertEquals(fileName, file.getFileName());
        assertEquals(filePath, file.getFilePath());
        assertEquals(fileType, file.getFileType());
        assertEquals(fileSize, file.getFileSize());
        assertEquals(fileFormat, file.getFileFormat());
        assertEquals(StatusConstants.DatasetFileStatuses.COMPLETED, file.getStatus());
        assertNull(file.getUploadTime());
        assertNull(file.getLastAccessTime());
    }

    @Test
    @DisplayName("gettersAndSetters: 基本属性访问")
    void testGettersAndSetters() {
        String id = "file-id-123";
        String datasetId = "dataset-id-456";
        String fileName = "document.pdf";
        String filePath = "/uploads/document.pdf";
        String fileType = "APPLICATION";
        Long fileSize = 2048L;
        String fileFormat = "pdf";
        LocalDateTime uploadTime = LocalDateTime.now();
        LocalDateTime lastAccessTime = LocalDateTime.now().minusDays(1);
        String status = StatusConstants.DatasetFileStatuses.PROCESSING;

        datasetFile.setId(id);
        datasetFile.setDatasetId(datasetId);
        datasetFile.setFileName(fileName);
        datasetFile.setFilePath(filePath);
        datasetFile.setFileType(fileType);
        datasetFile.setFileSize(fileSize);
        datasetFile.setFileFormat(fileFormat);
        datasetFile.setUploadTime(uploadTime);
        datasetFile.setLastAccessTime(lastAccessTime);
        datasetFile.setStatus(status);

        assertEquals(id, datasetFile.getId());
        assertEquals(datasetId, datasetFile.getDatasetId());
        assertEquals(fileName, datasetFile.getFileName());
        assertEquals(filePath, datasetFile.getFilePath());
        assertEquals(fileType, datasetFile.getFileType());
        assertEquals(fileSize, datasetFile.getFileSize());
        assertEquals(fileFormat, datasetFile.getFileFormat());
        assertEquals(uploadTime, datasetFile.getUploadTime());
        assertEquals(lastAccessTime, datasetFile.getLastAccessTime());
        assertEquals(status, datasetFile.getStatus());
    }

    @Test
    @DisplayName("setters: 设置null值")
    void testSettersWithNullValues() {
        // 先设置一些值
        datasetFile.setId("test-id");
        datasetFile.setFileName("test.txt");
        datasetFile.setFileSize(1024L);

        // 然后设置为null
        datasetFile.setId(null);
        datasetFile.setFileName(null);
        datasetFile.setFileSize(null);

        assertNull(datasetFile.getId());
        assertNull(datasetFile.getFileName());
        assertNull(datasetFile.getFileSize());
    }

    @Test
    @DisplayName("fileSize: 处理0和负数")
    void testFileSizeEdgeCases() {
        // 测试0大小
        datasetFile.setFileSize(0L);
        assertEquals(0L, datasetFile.getFileSize());

        // 测试大文件
        Long largeSize = Long.MAX_VALUE;
        datasetFile.setFileSize(largeSize);
        assertEquals(largeSize, datasetFile.getFileSize());
    }

    @Test
    @DisplayName("status: 不同状态值")
    void testDifferentStatusValues() {
        String[] statuses = {
                StatusConstants.DatasetFileStatuses.UPLOADED,
                StatusConstants.DatasetFileStatuses.PROCESSING,
                StatusConstants.DatasetFileStatuses.COMPLETED,
                StatusConstants.DatasetFileStatuses.ERROR
        };

        for (String status : statuses) {
            datasetFile.setStatus(status);
            assertEquals(status, datasetFile.getStatus());
        }
    }

    @Test
    @DisplayName("fileType: 不同文件类型")
    void testDifferentFileTypes() {
        String[] fileTypes = {"TEXT", "IMAGE", "VIDEO", "AUDIO", "APPLICATION"};

        for (String fileType : fileTypes) {
            datasetFile.setFileType(fileType);
            assertEquals(fileType, datasetFile.getFileType());
        }
    }

    @Test
    @DisplayName("timestamps: 时间戳设置和获取")
    void testTimestamps() {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime past = now.minusDays(1);
        LocalDateTime future = now.plusDays(1);

        datasetFile.setUploadTime(now);
        datasetFile.setLastAccessTime(past);

        assertEquals(now, datasetFile.getUploadTime());
        assertEquals(past, datasetFile.getLastAccessTime());

        // 测试更新访问时间
        datasetFile.setLastAccessTime(future);
        assertEquals(future, datasetFile.getLastAccessTime());
    }

    @Test
    @DisplayName("filePath: 不同路径格式")
    void testDifferentPathFormats() {
        String[] paths = {
                "/absolute/path/file.txt",
                "relative/path/file.txt",
                "C:\\Windows\\Path\\file.txt",
                "/home/user/documents/file.pdf",
                "./local/file.csv"
        };

        for (String path : paths) {
            datasetFile.setFilePath(path);
            assertEquals(path, datasetFile.getFilePath());
        }
    }

    @Test
    @DisplayName("fileName: 不同文件名格式")
    void testDifferentFileNames() {
        String[] fileNames = {
                "simple.txt",
                "file-with-dashes.csv",
                "file_with_underscores.json",
                "file with spaces.pdf",
                "文件名中文.docx",
                "file.with.multiple.dots.zip",
                "no-extension"
        };

        for (String fileName : fileNames) {
            datasetFile.setFileName(fileName);
            assertEquals(fileName, datasetFile.getFileName());
        }
    }

    @Test
    @DisplayName("constructor: 参数构造函数处理null值")
    void testParameterizedConstructorWithNulls() {
        DatasetFile file = new DatasetFile(null, null, null, null, null, null);

        assertNull(file.getDatasetId());
        assertNull(file.getFileName());
        assertNull(file.getFilePath());
        assertNull(file.getFileType());
        assertNull(file.getFileSize());
        assertNull(file.getFileFormat());
        assertEquals(StatusConstants.DatasetFileStatuses.COMPLETED, file.getStatus());
    }

    @Test
    @DisplayName("immutability: 对象状态变更")
    void testObjectStateChanges() {
        // 初始状态
        assertNull(datasetFile.getId());
        assertNull(datasetFile.getStatus());

        // 设置初始值
        datasetFile.setId("initial-id");
        datasetFile.setStatus(StatusConstants.DatasetFileStatuses.UPLOADED);
        
        assertEquals("initial-id", datasetFile.getId());
        assertEquals(StatusConstants.DatasetFileStatuses.UPLOADED, datasetFile.getStatus());

        // 更改值
        datasetFile.setId("new-id");
        datasetFile.setStatus(StatusConstants.DatasetFileStatuses.PROCESSING);

        assertEquals("new-id", datasetFile.getId());
        assertEquals(StatusConstants.DatasetFileStatuses.PROCESSING, datasetFile.getStatus());
    }
}
