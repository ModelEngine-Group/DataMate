package com.edatamate.domain.dataset.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Stream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

/**
 * 文件处理服务
 *
 * @author: dallas
 * @since: 2025-07-17
 */
@Service
public class FileService {
    private static final Logger logger = LoggerFactory.getLogger(FileService.class);

    @Value("${dataset.file.base-dir:/dataset}")
    private String targetDirectory;

    private static final String EMPTY_HASH = "0";

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

    /**
     * 文件上传到指定目录
     *
     * @param file 上传的文件
     * @param baseDir 基础目录
     * @return 存放文件的最终目录
     */
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


    public static String calculateFileHash(InputStream fis) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] buffer = new byte[8192];
            int bytesRead;
            while ((bytesRead = fis.read(buffer)) != -1) {
                digest.update(buffer, 0, bytesRead);
            }
            byte[] hashBytes = digest.digest();
            StringBuilder sb = new StringBuilder();
            for (byte b : hashBytes) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (Exception e) {
            logger.error("计算文件SHA-256哈希值失败:", e);
            return EMPTY_HASH;
        }
    }

    /**
     * 删除数据集目录
     *
     * @param datasetId 数据集ID
     */
    public void deleteFilesByDatasetId(Long datasetId) {
        Path datasetPath = Paths.get(targetDirectory, String.valueOf(datasetId));
        if (!Files.exists(datasetPath)) {
            return; // 不存在直接返回
        }
        try (Stream<Path> walk = Files.walk(datasetPath)) {
            walk.sorted(Comparator.reverseOrder()).forEach(path -> {
                try {
                    Files.delete(path);
                } catch (IOException e) {
                    logger.error("删除文件或目录失败, 路径: {}, 错误信息: {}", path, e.getMessage());
                    throw new RuntimeException("删除文件或目录失败: " + path, e);
                }
            });
        } catch (IOException e) {
            throw new RuntimeException("删除数据集目录及其内容失败: " + datasetPath, e);
        }
    }

    /**
     * 删除数据集中文件
     *
     * @param paths 要删除的files的路径列表
     */
    public void batchDeleteFilesByIds(List<String> paths) {
        if (paths == null || paths.isEmpty()) {
            return; // 没有要删除的文件
        }
        for (String pathStr : paths) {
            Path path = Paths.get(pathStr);
            if (!Files.exists(path)) {
                logger.warn("文件不存在, 跳过删除: {}", pathStr);
                continue;
            }
            try {
                Files.delete(path);
            } catch (IOException e) {
                logger.error("删除文件失败, 路径: {}, 错误信息: {}", pathStr, e.getMessage());
                throw new RuntimeException("删除文件失败: " + pathStr, e);
            }
        }
    }

    /**
     * 压缩指定文件到Zip输出流中
     *
     * @param filePath 要压缩的文件路径
     * @param zos Zip输出流
     * @param fileName 压缩包中的文件名
     */
    public void zipFile(String filePath, ZipOutputStream zos, String fileName) throws IOException {
        Path path = Paths.get(filePath);
        if (!Files.exists(path)) {
            logger.warn("文件不存在: {}", filePath);
        }
        try (InputStream fis = Files.newInputStream(path);
             BufferedInputStream bis = new BufferedInputStream(fis)) {
            ZipEntry zipEntry = new ZipEntry(fileName);
            zos.putNextEntry(zipEntry);
            byte[] buffer = new byte[8192];
            int len;
            while ((len = bis.read(buffer)) > 0) {
                zos.write(buffer, 0, len);
            }
            zos.closeEntry();
        }
    }
}