package com.edatamate.infrastructure.utils;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import lombok.extern.slf4j.Slf4j;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Map;


@Slf4j
public class FileUtil {
    public static void writePrettyJson(Map<String, Object> map, String filepath) {
        ObjectMapper objectMapper = new ObjectMapper();
        // 启用格式化输出
        objectMapper.enable(SerializationFeature.INDENT_OUTPUT);

        try {
            Path path = Paths.get(filepath);
            Path parentDir = path.getParent();

            if (parentDir != null) {
                Files.createDirectories(parentDir);
            }
            objectMapper.writeValue(new File(filepath), map);
            log.info("格式化的 JSON 已写入: {}", filepath);
        } catch (IOException e) {
            log.error("写入失败: {}", e.getMessage());
        }
    }

    public static boolean deleteFile(String filepath) {
        if (filepath == null || filepath.isEmpty()) {
            return false;
        }

        File file = new File(filepath);
        return file.delete();
    }
}
