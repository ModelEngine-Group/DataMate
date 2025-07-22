package com.edatamate.common.dataset.utils;

import com.edatamate.common.dataset.DatasetFile;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;

/**
 * 扫描本地文件元数据的工具类。
 *
 * @since 2025-07-22
 */
public class LocalScannerUtils {
    private static final String EMPTY_HASH = "0";

    private static final Logger logger = LoggerFactory.getLogger(LocalScannerUtils.class);

    public static List<DatasetFile> scanDatasetFiles(String datasetPath, Long datasetId) throws IOException {
        List<DatasetFile> fileList = new ArrayList<>();
        Path rootPath = Paths.get(datasetPath);
        try (Stream<Path> paths = Files.walk(rootPath)) {
            paths.filter(Files::isRegularFile).forEach(path -> {
                DatasetFile file = new DatasetFile();
                file.setDatasetId(datasetId);
                file.setName(path.getFileName().toString());
                file.setPath(path.toString());
                file.setSize(path.toFile().length());
                file.setType(FileUtils.getFileSuffix(path.getFileName().toString()));
                file.setStatus("active");
                file.setParentId(0L);
                file.setSourceFile(path.getFileName().toString());
                file.setCreatedTime(LocalDateTime.now());
                file.setUpdatedTime(LocalDateTime.now());
                fileList.add(file);
            });
        }
        fileList.forEach(file -> {
            try (var inputStream = Files.newInputStream(Paths.get(file.getPath()))) {
                file.setHash(FileUtils.calculateFileHash(inputStream));
            } catch (IOException e) {
                logger.error("Failed to calculate sha256: {}", e.getMessage());
                file.setHash(EMPTY_HASH);
            }
        });
        return fileList;
    }
}
