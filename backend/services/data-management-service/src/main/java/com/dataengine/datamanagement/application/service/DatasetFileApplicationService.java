package com.dataengine.datamanagement.application.service;

import com.dataengine.datamanagement.domain.model.dataset.Dataset;
import com.dataengine.datamanagement.domain.model.dataset.DatasetFile;
import com.dataengine.datamanagement.domain.model.dataset.DatasetFileStatus;
import com.dataengine.datamanagement.domain.repository.DatasetFileRepository;
import com.dataengine.datamanagement.domain.repository.DatasetRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.data.domain.Page;
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
import java.util.UUID;

/**
 * 数据集文件应用服务
 */
@Service
@Transactional
public class DatasetFileApplicationService {

    private final DatasetFileRepository datasetFileRepository;
    private final DatasetRepository datasetRepository;
    private final Path fileStorageLocation;

    @Autowired
    public DatasetFileApplicationService(DatasetFileRepository datasetFileRepository,
                                       DatasetRepository datasetRepository,
                                       @Value("${app.file.upload-dir:./uploads}") String uploadDir) {
        this.datasetFileRepository = datasetFileRepository;
        this.datasetRepository = datasetRepository;
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
        Dataset dataset = datasetRepository.findById(datasetId)
            .orElseThrow(() -> new IllegalArgumentException("Dataset not found: " + datasetId));

        // 生成唯一文件名
        String fileId = UUID.randomUUID().toString();
        String originalFilename = file.getOriginalFilename();
        String fileExtension = getFileExtension(originalFilename);
        String fileName = fileId + fileExtension;
        
        // 保存文件到磁盘
        try {
            Path targetLocation = this.fileStorageLocation.resolve(fileName);
            Files.copy(file.getInputStream(), targetLocation, StandardCopyOption.REPLACE_EXISTING);
            
            // 创建文件实体
            DatasetFile datasetFile = new DatasetFile(
                fileId,
                fileName,
                originalFilename,
                file.getContentType(),
                file.getSize(),
                description,
                targetLocation.toString(),
                uploadedBy,
                dataset
            );
            
            // 保存到数据库
            datasetFile = datasetFileRepository.save(datasetFile);
            
            // 更新数据集文件信息
            dataset.addFile(datasetFile);
            datasetRepository.save(dataset);
            
            return datasetFile;
            
        } catch (IOException ex) {
            throw new RuntimeException("Could not store file " + fileName, ex);
        }
    }

    /**
     * 获取数据集文件列表
     */
    @Transactional(readOnly = true)
    public Page<DatasetFile> getDatasetFiles(String datasetId, String fileType, 
                                           DatasetFileStatus status, Pageable pageable) {
        return datasetFileRepository.findByCriteria(datasetId, fileType, status, pageable);
    }

    /**
     * 获取文件详情
     */
    @Transactional(readOnly = true)
    public DatasetFile getDatasetFile(String datasetId, String fileId) {
        DatasetFile file = datasetFileRepository.findById(fileId)
            .orElseThrow(() -> new IllegalArgumentException("File not found: " + fileId));
        
        if (!file.getDataset().getId().equals(datasetId)) {
            throw new IllegalArgumentException("File does not belong to the specified dataset");
        }
        
        return file;
    }

    /**
     * 删除文件
     */
    public void deleteDatasetFile(String datasetId, String fileId) {
        DatasetFile file = getDatasetFile(datasetId, fileId);
        Dataset dataset = file.getDataset();
        
        // 从磁盘删除文件
        try {
            Path filePath = Paths.get(file.getFilePath());
            Files.deleteIfExists(filePath);
        } catch (IOException ex) {
            // 记录日志但不抛出异常，继续删除数据库记录
        }
        
        // 从数据库删除
        datasetFileRepository.delete(file);
        
        // 更新数据集文件信息
        dataset.removeFile(file);
        datasetRepository.save(dataset);
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

    /**
     * 更新文件状态
     */
    public DatasetFile updateFileStatus(String datasetId, String fileId, DatasetFileStatus status) {
        DatasetFile file = getDatasetFile(datasetId, fileId);
        file.updateStatus(status);
        
        // 更新数据集完成率
        Dataset dataset = file.getDataset();
        datasetRepository.save(dataset);
        
        return datasetFileRepository.save(file);
    }

    /**
     * 获取文件扩展名
     */
    private String getFileExtension(String fileName) {
        if (fileName == null || fileName.isEmpty()) {
            return "";
        }
        
        int lastDotIndex = fileName.lastIndexOf(".");
        if (lastDotIndex == -1) {
            return "";
        }
        
        return fileName.substring(lastDotIndex);
    }
}
