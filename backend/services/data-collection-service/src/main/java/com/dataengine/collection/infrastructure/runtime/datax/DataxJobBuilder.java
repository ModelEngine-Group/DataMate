package com.dataengine.collection.infrastructure.runtime.datax;

import com.dataengine.collection.domain.model.CollectionTask;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * 根据任务配置拼装 DataX 作业 JSON 文件
 */
@Component
@RequiredArgsConstructor
public class DataxJobBuilder {

    private final DataxProperties props;

    public Path buildJobFile(CollectionTask task) throws IOException {
        Files.createDirectories(Paths.get(props.getJobConfigPath()));
        String fileName = String.format("datax-job-%s.json", task.getId());
        Path path = Paths.get(props.getJobConfigPath(), fileName);
        // 简化：直接将任务中的 config 字段作为 DataX 作业 JSON
        try (FileWriter fw = new FileWriter(path.toFile())) {
            String json = task.getConfig() == null || task.getConfig().isEmpty() ?
                    defaultJobJson() : task.getConfig();
            fw.write(json);
        }
        return path;
    }

    private String defaultJobJson() {
        // 提供一个最小可运行的空 job，实际会被具体任务覆盖
        return "{\n  \"job\": {\n    \"setting\": {\n      \"speed\": {\n        \"channel\": 1\n      }\n    },\n    \"content\": []\n  }\n}";
    }
}
