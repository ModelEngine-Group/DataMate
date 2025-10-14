package com.dataengine.common.domain.utils;

import java.io.File;

/**
 * 通用工具类
 */
public class CommonUtils {
    /**
     * 从文件路径中获取文件名（带后缀）
     *
     * @param filePath 文件路径
     * @return 文件名（带后缀）
     */
    public static String trimFilePath(String filePath) {
        int lastSlashIndex = filePath.lastIndexOf(File.separator);

        String filename = filePath;
        if (lastSlashIndex != -1) {
            filename = filePath.substring(lastSlashIndex + 1);
        }
        return filename;
    }
}
