package com.dataengine.datamanagement.application.service;

import com.dataengine.datamanagement.domain.model.dataset.Dataset;
import com.dataengine.datamanagement.domain.model.dataset.DatasetFile;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.DatasetFileMapper;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.DatasetMapper;
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

import java.io.IOException;
import java.net.MalformedURLException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

/**
 * 数据集文件应用服务（UUID 模式）
 */
@Service
@Transactional
public class DatasetFileApplicationService {

    private final DatasetFileMapper datasetFileMapper;
    private final DatasetMapper datasetMapper;
    private final Path fileStorageLocation;

    @Autowired
    public DatasetFileApplicationService(DatasetFileMapper datasetFileMapper,
                                       DatasetMapper datasetMapper,
                                       @Value("${app.file.upload-dir:./uploads}") String uploadDir) {
        this.datasetFileMapper = datasetFileMapper;
        this.datasetMapper = datasetMapper;
        this.fileStorageLocation = Paths.get(uploadDir).toAbsolutePath().normalize();
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
        String fileName = System.currentTimeMillis() + "_" + (originalFilename != null ? originalFilename : "file");
        try {
            // 保存文件到磁盘
            Path targetLocation = this.fileStorageLocation.resolve(fileName);
            Files.copy(file.getInputStream(), targetLocation, StandardCopyOption.REPLACE_EXISTING);

            // 创建文件实体（UUID 主键）
            DatasetFile datasetFile = new DatasetFile();
            datasetFile.setId(UUID.randomUUID().toString());
            datasetFile.setDatasetId(datasetId);
            datasetFile.setFileName(fileName);
            datasetFile.setFilePath(targetLocation.toString());
            datasetFile.setFileType(file.getContentType());
            datasetFile.setFileFormat(getFileExtension(originalFilename));
            datasetFile.setFileSize(file.getSize());
            datasetFile.setUploadTime(LocalDateTime.now());
            datasetFile.setStatus("ACTIVE");

            // 保存到数据库
            datasetFileMapper.insert(datasetFile);

            // 更新数据集统计
            dataset.addFile(datasetFile);
            datasetMapper.update(dataset);

            return datasetFileMapper.findByDatasetIdAndFileName(datasetId, fileName);

        } catch (IOException ex) {
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
}
