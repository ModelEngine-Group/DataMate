package com.dataengine.datamanagement.application.service;

import com.dataengine.datamanagement.domain.model.dataset.DatasetFile;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * 文件元数据扫描服务
 */
@Slf4j
@Service
public class FileMetadataService {

    /**
     * 扫描文件路径列表，提取文件元数据
     * @param filePaths 文件路径列表
     * @param datasetId 数据集ID
     * @return 数据集文件列表
     */
    public List<DatasetFile> scanFiles(List<String> filePaths, String datasetId) {
        List<DatasetFile> datasetFiles = new ArrayList<>();
        
        if (filePaths == null || filePaths.isEmpty()) {
            log.warn("文件路径列表为空，跳过扫描");
            return datasetFiles;
        }
        
        for (String filePath : filePaths) {
            try {
                DatasetFile datasetFile = extractFileMetadata(filePath, datasetId);
                if (datasetFile != null) {
                    datasetFiles.add(datasetFile);
                }
            } catch (Exception e) {
                log.error("扫描文件失败: {}, 错误: {}", filePath, e.getMessage(), e);
            }
        }
        
        log.info("文件扫描完成，共扫描 {} 个文件", datasetFiles.size());
        return datasetFiles;
    }
    
    /**
     * 提取单个文件的元数据
     * @param filePath 文件路径
     * @param datasetId 数据集ID
     * @return 数据集文件对象
     */
    private DatasetFile extractFileMetadata(String filePath, String datasetId) throws IOException {
        Path path = Paths.get(filePath);
        
        if (!Files.exists(path)) {
            log.warn("文件不存在: {}", filePath);
            return null;
        }
        
        if (!Files.isRegularFile(path)) {
            log.warn("路径不是文件: {}", filePath);
            return null;
        }
        
        String fileName = path.getFileName().toString();
        long fileSize = Files.size(path);
        String fileFormat = getFileExtension(fileName);
        String fileType = determineFileType(fileFormat);
        
        return DatasetFile.builder()
                .id(UUID.randomUUID().toString())
                .datasetId(datasetId)
                .fileName(fileName)
                .filePath(filePath)
                .fileSize(fileSize)
                .fileFormat(fileFormat)
                .fileType(fileType)
                .uploadTime(LocalDateTime.now())
                .lastAccessTime(LocalDateTime.now())
                .status("UPLOADED")
                .build();
    }
    
    /**
     * 获取文件扩展名
     */
    private String getFileExtension(String fileName) {
        int lastDotIndex = fileName.lastIndexOf('.');
        if (lastDotIndex > 0 && lastDotIndex < fileName.length() - 1) {
            return fileName.substring(lastDotIndex + 1).toLowerCase();
        }
        return "unknown";
    }
    
    /**
     * 根据文件扩展名判断文件类型
     */
    private String determineFileType(String fileFormat) {
        if (fileFormat == null) {
            return "UNKNOWN";
        }
        
        // 图片类型
        if (fileFormat.matches("jpg|jpeg|png|gif|bmp|webp|svg|tiff|ico")) {
            return "IMAGE";
        }
        
        // 视频类型
        if (fileFormat.matches("mp4|avi|mov|wmv|flv|mkv|webm|m4v")) {
            return "VIDEO";
        }
        
        // 音频类型
        if (fileFormat.matches("mp3|wav|flac|aac|ogg|wma|m4a")) {
            return "AUDIO";
        }
        
        // 文本类型
        if (fileFormat.matches("txt|md|json|xml|csv|log|yaml|yml|properties|conf")) {
            return "TEXT";
        }
        
        // 文档类型
        if (fileFormat.matches("pdf|doc|docx|xls|xlsx|ppt|pptx")) {
            return "DOCUMENT";
        }
        
        return "OTHER";
    }
}
