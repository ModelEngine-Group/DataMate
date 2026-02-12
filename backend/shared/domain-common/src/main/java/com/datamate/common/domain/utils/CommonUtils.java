package com.datamate.common.domain.utils;

import java.io.File;
import java.util.UUID;

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

    /**
     * 判断字符串是否是uuid
     *
     * @param str 要判断的字符串
     * @return 判断结果
     */
    public static boolean isUUID(String str) {
        if (str == null) return false;
        try {
            UUID.fromString(str);
            return true;
        } catch (IllegalArgumentException e) {
            return false;
        }
    }
}
