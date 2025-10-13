package com.dataengine.common.domain.utils;

import org.springframework.util.StringUtils;

import java.util.Collections;
import java.util.List;
import java.util.Locale;

/**
 * 解析工具类
 */
public class AnalyzerUtils {
    /** zip压缩包文件后缀类型 */
    public static final String TYPE_ZIP = "zip";

    /** tar压缩包文件后缀类型 */
    public static final String TYPE_TAR_GZ = "tar.gz";

    private static final List<String> SPECIAL_EXTENSIONS = Collections.singletonList(TYPE_TAR_GZ);

    /**
     * 从文件路径获取文件后缀类型
     *
     * @param filePath 文件类型
     * @return 文件后缀类型
     */
    public static String getExtension(final String filePath) {
        String filename = CommonUtils.trimFilePath(filePath);
        for (String ext : SPECIAL_EXTENSIONS) {
            if (StringUtils.endsWithIgnoreCase(filename, "." + ext)) {
                return ext;
            }
        }
        int firstDotIndex = filename.lastIndexOf(".");
        if (firstDotIndex == -1) {
            return "";
        }
        return filename.substring(firstDotIndex + 1).toLowerCase(Locale.ROOT);
    }
}
