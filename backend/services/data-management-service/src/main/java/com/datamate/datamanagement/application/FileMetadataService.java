package com.datamate.datamanagement.application;

import com.datamate.datamanagement.domain.model.dataset.DatasetFile;
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
                Path path = Paths.get(filePath);

                if (!Files.exists(path)) {
                    log.warn("路径不存在: {}", filePath);
                    continue;
                }

                if (Files.isDirectory(path)) {
                    scanDirectory(datasetId, filePath, path, datasetFiles);
                } else {
                    // 如果是文件，直接处理
                    DatasetFile datasetFile = extractFileMetadata(filePath, datasetId);
                    if (datasetFile != null) {
                        datasetFiles.add(datasetFile);
                    }
                }
            } catch (Exception e) {
                log.error("扫描路径失败: {}, 错误: {}", filePath, e.getMessage(), e);
            }
        }

        log.info("文件扫描完成，共扫描 {} 个文件", datasetFiles.size());
        return datasetFiles;
    }

    private void scanDirectory(String datasetId, String filePath, Path path,
                               List<DatasetFile> datasetFiles) throws IOException {
        // 如果是目录，扫描该目录下的所有文件（非递归）
        List<Path> filesInDir = Files.list(path)
                .filter(Files::isRegularFile)
                .toList();

        for (Path file : filesInDir) {
            try {
                DatasetFile datasetFile = extractFileMetadata(file.toString(), datasetId);
                if (datasetFile != null) {
                    datasetFiles.add(datasetFile);
                }
            } catch (Exception e) {
                log.error("处理目录中的文件失败: {}, 错误: {}", file, e.getMessage(), e);
            }
        }
        log.info("已扫描目录 {} 下的 {} 个文件", filePath, filesInDir.size());
    }
    /**
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
        String fileType = getFileExtension(fileName);

        return DatasetFile.builder()
                .id(UUID.randomUUID().toString())
                .datasetId(datasetId)
                .fileName(fileName)
                .filePath(filePath)
                .fileSize(fileSize)
                .fileType(fileType)
                .uploadTime(LocalDateTime.now())
                .lastAccessTime(LocalDateTime.now())
                .status("ACTIVE")
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
}
