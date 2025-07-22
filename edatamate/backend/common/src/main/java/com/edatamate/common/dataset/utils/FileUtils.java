package com.edatamate.common.dataset.utils;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.InputStream;
import java.security.MessageDigest;

/**
 * 文件处理工具类
 *
 * @since 2025-07-22
 */
public class FileUtils {
    private static final Logger logger = LoggerFactory.getLogger(FileUtils.class);

    private static final String EMPTY_HASH = "0";

    /**
     * 计算文件的SHA-256哈希值
     * @param fis 文件流
     * @return 哈希值
     */
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
     * 根据文件名获取文件后缀格式
     * @param fileName 文件名
     * @return 文件后缀
     */
    public static String getFileSuffix(String fileName) {
        int idx = fileName.lastIndexOf('.');
        return (idx > 0 && idx < fileName.length() - 1) ? fileName.substring(idx + 1) : "";
    }
}
