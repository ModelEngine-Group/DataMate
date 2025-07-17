package com.edatamate.domain.service;

import cn.hutool.core.util.HashUtil;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.util.Comparator;

/**
 * 文件处理服务
 *
 * @author: dallas
 * @since: 2025-07-17
 */
@Service
public class FileService {
    @Value("${dataset.file.base-dir:/dataset}")
    private String targetDirectory;

    /**
     * 初始化数据集目录
     *
     * @param datasetId 数据集ID
     * @return 数据集目录路径
     */
    public String initDatasetDirectory(Long datasetId) {
        Path datasetPath = Paths.get(targetDirectory, String.valueOf(datasetId));
        try {
            if (!Files.exists(datasetPath)) {
                Files.createDirectories(datasetPath);
            }
            return datasetPath.toString();
        } catch (IOException e) {
            throw new RuntimeException("数据集目录初始化失败", e);
        }
    }

    public String uploadFileToDataset(MultipartFile file, String baseDir) {
        String fileName = file.getOriginalFilename();
        Path targetPath = Paths.get(baseDir, fileName);
        try {
            Files.copy(file.getInputStream(), targetPath, StandardCopyOption.REPLACE_EXISTING);
            return targetPath.toString();
        } catch (IOException e) {
            throw new RuntimeException("文件上传失败", e);
        }
    }


    public String calculateFileHash(MultipartFile file) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            try (var inputStream = file.getInputStream()) {
                byte[] buffer = new byte[8192];
                int bytesRead;
                while ((bytesRead = inputStream.read(buffer)) != -1) {
                    digest.update(buffer, 0, bytesRead);
                }
            }
            byte[] hashBytes = digest.digest();
            StringBuilder sb = new StringBuilder();
            for (byte b : hashBytes) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (Exception e) {
            throw new RuntimeException("计算文件SHA-256哈希值失败", e);
        }
    }

    /**
     * 删除数据集目录
     *
     * @param datasetId 数据集ID
     */
    public void deleteFilesByDatasetId(Long datasetId) {
        Path datasetPath = Paths.get(targetDirectory, String.valueOf(datasetId));
        try {
            if (Files.exists(datasetPath)) {
                Files.walk(datasetPath).sorted(Comparator.reverseOrder()).forEach(path -> {
                    try {
                        Files.delete(path);
                    } catch (IOException e) {
                        throw new RuntimeException("删除文件或目录失败: " + path, e);
                    }
                });
            }
        } catch (IOException e) {
            throw new RuntimeException("删除数据集目录及其内容失败", e);
        }
    }
}
