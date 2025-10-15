package com.dataengine.datamanagement.application.service;

import com.dataengine.common.domain.model.ChunkUploadPreRequest;
import com.dataengine.common.domain.model.FileUploadResult;
import com.dataengine.common.domain.service.FileService;
import com.dataengine.common.domain.utils.AnalyzerUtils;
import com.dataengine.datamanagement.domain.contants.DatasetConstant;
import com.dataengine.datamanagement.domain.model.dataset.Dataset;
import com.dataengine.datamanagement.domain.model.dataset.DatasetFile;
import com.dataengine.datamanagement.domain.model.dataset.DatasetFileUploadCheckInfo;
import com.dataengine.datamanagement.domain.model.dataset.StatusConstants;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.DatasetFileMapper;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.DatasetMapper;
import com.dataengine.datamanagement.interfaces.converter.DatasetConverter;
import com.dataengine.datamanagement.interfaces.dto.UploadFileRequest;
import com.dataengine.datamanagement.interfaces.dto.UploadFilesPreRequest;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.apache.ibatis.session.RowBounds;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

/**
 * 数据集文件应用服务（UUID 模式）
 */
@Slf4j
@Service
@Transactional
public class DatasetFileApplicationService {

    private final DatasetFileMapper datasetFileMapper;
    private final DatasetMapper datasetMapper;
    private final Path fileStorageLocation;
    private final FileService fileService;

    @Value("${dataset.base.path:/dataset}")
    private String datasetBasePath;

    @Autowired
    public DatasetFileApplicationService(DatasetFileMapper datasetFileMapper,
                                       DatasetMapper datasetMapper, FileService fileService,
                                       @Value("${app.file.upload-dir:./dataset}") String uploadDir) {
        this.datasetFileMapper = datasetFileMapper;
        this.datasetMapper = datasetMapper;
        this.fileStorageLocation = Paths.get(uploadDir).toAbsolutePath().normalize();
        this.fileService = fileService;
        try {
            Files.createDirectories(this.fileStorageLocation);
        } catch (Exception ex) {
            throw new RuntimeException("Could not create the directory where the uploaded files will be stored.", ex);
        }
    }

    /**
     * 上传文件到数据集
     */
    public DatasetFile uploadFile(String datasetId, MultipartFile file, String description, String uploadedBy) {
        Dataset dataset = datasetMapper.findById(datasetId);
        if (dataset == null) {
            throw new IllegalArgumentException("Dataset not found: " + datasetId);
        }

        String originalFilename = file.getOriginalFilename();
        String fileName = originalFilename != null ? originalFilename : "file";
        try {
            // 保存文件到磁盘
            Path targetLocation = this.fileStorageLocation.resolve(datasetId + File.separator + fileName);
            // 确保目标目录存在
            Files.createDirectories(targetLocation);
            Files.copy(file.getInputStream(), targetLocation, StandardCopyOption.REPLACE_EXISTING);

            // 创建文件实体（UUID 主键）
            DatasetFile datasetFile = new DatasetFile();
            datasetFile.setId(UUID.randomUUID().toString());
            datasetFile.setDatasetId(datasetId);
            datasetFile.setFileName(fileName);
            datasetFile.setFilePath(targetLocation.toString());
            datasetFile.setFileType(getFileExtension(originalFilename));
            datasetFile.setFileFormat(file.getContentType());
            datasetFile.setFileSize(file.getSize());
            datasetFile.setUploadTime(LocalDateTime.now());
            datasetFile.setStatus(StatusConstants.DatasetFileStatuses.COMPLETED);

            // 保存到数据库
            datasetFileMapper.insert(datasetFile);

            // 更新数据集统计
            dataset.addFile(datasetFile);
            datasetMapper.update(dataset);

            return datasetFileMapper.findByDatasetIdAndFileName(datasetId, fileName);

        } catch (IOException ex) {
            log.error("Could not store file {}", fileName, ex);
            throw new RuntimeException("Could not store file " + fileName, ex);
        }
    }

    /**
     * 获取数据集文件列表
     */
    @Transactional(readOnly = true)
    public Page<DatasetFile> getDatasetFiles(String datasetId, String fileType,
                                           String status, Pageable pageable) {
        RowBounds bounds = new RowBounds(pageable.getPageNumber() * pageable.getPageSize(), pageable.getPageSize());
        List<DatasetFile> content = datasetFileMapper.findByCriteria(datasetId, fileType, status, bounds);
        long total = content.size() < pageable.getPageSize() && pageable.getPageNumber() == 0 ? content.size() : content.size() + (long) pageable.getPageNumber() * pageable.getPageSize();
        return new PageImpl<>(content, pageable, total);
    }

    /**
     * 获取文件详情
     */
    @Transactional(readOnly = true)
    public DatasetFile getDatasetFile(String datasetId, String fileId) {
        DatasetFile file = datasetFileMapper.findById(fileId);
        if (file == null) {
            throw new IllegalArgumentException("File not found: " + fileId);
        }
        if (!file.getDatasetId().equals(datasetId)) {
            throw new IllegalArgumentException("File does not belong to the specified dataset");
        }
        return file;
    }

    /**
     * 删除文件
     */
    public void deleteDatasetFile(String datasetId, String fileId) {
        DatasetFile file = getDatasetFile(datasetId, fileId);
        try {
            Path filePath = Paths.get(file.getFilePath());
            Files.deleteIfExists(filePath);
        } catch (IOException ex) {
            // ignore
        }
        datasetFileMapper.deleteById(fileId);

        Dataset dataset = datasetMapper.findById(datasetId);
        // 简单刷新统计（精确处理可从DB统计）
        dataset.setFileCount(Math.max(0, dataset.getFileCount() - 1));
        dataset.setSizeBytes(Math.max(0, dataset.getSizeBytes() - (file.getFileSize() != null ? file.getFileSize() : 0)));
        datasetMapper.update(dataset);
    }

    /**
     * 下载文件
     */
    @Transactional(readOnly = true)
    public Resource downloadFile(String datasetId, String fileId) {
        DatasetFile file = getDatasetFile(datasetId, fileId);
        try {
            Path filePath = Paths.get(file.getFilePath()).normalize();
            Resource resource = new UrlResource(filePath.toUri());
            if (resource.exists()) {
                return resource;
            } else {
                throw new RuntimeException("File not found: " + file.getFileName());
            }
        } catch (MalformedURLException ex) {
            throw new RuntimeException("File not found: " + file.getFileName(), ex);
        }
    }

    private String getFileExtension(String fileName) {
        if (fileName == null || fileName.isEmpty()) {
            return null;
        }
        int lastDotIndex = fileName.lastIndexOf(".");
        if (lastDotIndex == -1) {
            return null;
        }
        return fileName.substring(lastDotIndex + 1);
    }

    /**
     * 预上传
     *
     * @param chunkUploadRequest 上传请求
     * @param datasetId 数据集id
     * @return 请求id
     */
    @Transactional
    public String preUpload(UploadFilesPreRequest chunkUploadRequest, String datasetId) {
        ChunkUploadPreRequest request = ChunkUploadPreRequest.builder().build();
        request.setUploadPath(datasetBasePath + File.separator + datasetId);
        request.setTotalFileNum(chunkUploadRequest.getTotalFileNum());
        request.setServiceId(DatasetConstant.SERVICE_ID);
        DatasetFileUploadCheckInfo checkInfo = new DatasetFileUploadCheckInfo();
        checkInfo.setDatasetId(datasetId);
        checkInfo.setHasArchive(chunkUploadRequest.isHasArchive());
        try {
            ObjectMapper objectMapper = new ObjectMapper();
            String checkInfoJson = objectMapper.writeValueAsString(checkInfo);
            request.setCheckInfo(checkInfoJson);
        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("Failed to serialize checkInfo to JSON", e);
        }
        return fileService.preUpload(request);
    }

    /**
     * 切片上传
     *
     * @param uploadFileRequest 上传请求
     */
    public void chunkUpload(String datasetId, UploadFileRequest uploadFileRequest) {
        FileUploadResult uploadResult = fileService.chunkUpload(DatasetConverter.INSTANCE.toChunkUploadRequest(uploadFileRequest));
        saveFileInfoToDb(uploadResult, uploadFileRequest, datasetId);
        if (uploadResult.isAllFilesUploaded()) {
            // 解析文件，后续依据需求看是否添加校验文件元数据和解析半结构化文件的逻辑，
        }
    }

    private void saveFileInfoToDb(FileUploadResult fileUploadResult, UploadFileRequest uploadFile, String datasetId) {
        if (Objects.isNull(fileUploadResult.getSavedFile())) {
            // 文件切片上传没有完成
            return;
        }
        File savedFile = fileUploadResult.getSavedFile();
        LocalDateTime currentTime = LocalDateTime.now();
        DatasetFile datasetFile = DatasetFile.builder()
            .id(UUID.randomUUID().toString())
            .datasetId(datasetId)
            .fileSize(savedFile.length())
            .uploadTime(currentTime)
            .lastAccessTime(currentTime)
            .fileName(uploadFile.getFileName())
            .filePath(savedFile.getPath())
            .fileType(AnalyzerUtils.getExtension(uploadFile.getFileName()))
            .build();

        datasetFileMapper.insert(datasetFile);
    }
}
