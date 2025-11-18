// java
package com.datamate.collection.infrastructure.datax;

import com.datamate.collection.common.enums.TemplateType;
import com.datamate.collection.domain.model.entity.CollectionTask;
import com.datamate.collection.domain.process.ProcessRunner;
import com.datamate.collection.infrastructure.datax.config.MysqlConfig;
import com.datamate.collection.infrastructure.datax.config.NasConfig;
import com.datamate.collection.infrastructure.datax.config.ObsConfig;
import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.exec.*;
import org.apache.commons.io.output.TeeOutputStream;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Component;

import java.io.*;
import java.nio.file.*;
import java.time.Duration;
import java.util.*;
import java.util.regex.Pattern;

@Slf4j
@Component
@RequiredArgsConstructor
public class DataxProcessRunner implements ProcessRunner {

    private final DataxProperties props;

    @Override
    public int runJob(CollectionTask task, String executionId, int timeoutSeconds) throws Exception {
        Path job = buildJobFile(task);
        int code = runJob(job.toFile(), executionId, Duration.ofSeconds(timeoutSeconds));
        // 任务成功后做后处理（仅针对 MYSQL 类型）
        postProcess(task);
        return code;
    }

    private int runJob(File jobFile, String executionId, Duration timeout) throws Exception {
        File logFile = new File(props.getLogPath(), String.format("datax-%s.log", executionId));
        String python = props.getPythonPath();
        String dataxPy = props.getHomePath() + File.separator + "bin" + File.separator + "datax.py";
        String cmd = String.format("%s %s %s", python, dataxPy, jobFile.getAbsolutePath());

        log.info("Execute DataX: {}", cmd);

        CommandLine cl = CommandLine.parse(cmd);
        DefaultExecutor executor = getExecutor(timeout, logFile);

        return executor.execute(cl);
    }

    private static DefaultExecutor getExecutor(Duration timeout, File logFile) throws FileNotFoundException {
        DefaultExecutor executor = new DefaultExecutor();

        // 将日志追加输出到文件
        File parent = logFile.getParentFile();
        if (!parent.exists()) {
            parent.mkdirs();
        }

        ExecuteStreamHandler streamHandler = new PumpStreamHandler(
            new TeeOutputStream(new FileOutputStream(logFile, true), System.out),
            new TeeOutputStream(new FileOutputStream(logFile, true), System.err)
        );
        executor.setStreamHandler(streamHandler);

        ExecuteWatchdog watchdog = new ExecuteWatchdog(timeout.toMillis());
        executor.setWatchdog(watchdog);
        return executor;
    }

    private Path buildJobFile(CollectionTask task) throws IOException {
        Files.createDirectories(Paths.get(props.getJobConfigPath()));
        String fileName = String.format("datax-job-%s.json", task.getId());
        Path path = Paths.get(props.getJobConfigPath(), fileName);
        // 简化：直接将任务中的 config 字段作为 DataX 作业 JSON
        try (FileWriter fw = new FileWriter(path.toFile())) {
            if (StringUtils.isBlank(task.getConfig())) {
                throw BusinessException.of(SystemErrorCode.UNKNOWN_ERROR);
            }
            String json = getJobConfig(task);
            log.info("Job config: {}", json);
            fw.write(json);
        }
        return path;
    }

    private String getJobConfig(CollectionTask task) {
        try {
            ObjectMapper objectMapper = new ObjectMapper();
            TemplateType templateType = task.getTaskType();
            return switch (templateType) {
                case NAS -> {
                    // NAS 特殊处理
                    NasConfig nasConfig = objectMapper.readValue(task.getConfig(), NasConfig.class);
                    yield nasConfig.toJobConfig(objectMapper, task);
                }
                case OBS -> {
                    ObsConfig obsConfig = objectMapper.readValue(task.getConfig(), ObsConfig.class);
                    yield obsConfig.toJobConfig(objectMapper, task);
                }
                case MYSQL -> {
                    MysqlConfig mysqlConfig = objectMapper.readValue(task.getConfig(), MysqlConfig.class);
                    yield mysqlConfig.toJobConfig(objectMapper, task);
                }
            };
        } catch (Exception e) {
            log.error("Failed to parse task config", e);
            throw new RuntimeException("Failed to parse task config", e);
        }
    }

    private void postProcess(CollectionTask task) throws IOException {
        if (task.getTaskType() != TemplateType.MYSQL) {
            return;
        }
        String targetPath = task.getTargetPath();
        // 将targetPath下所有不以.csv结尾的文件修改为以.csv结尾
        Path dir = Paths.get(targetPath);
        if (!Files.exists(dir) || !Files.isDirectory(dir)) {
            log.info("Target path {} does not exist or is not a directory for task {}, skip post processing.", targetPath, task.getId());
            return;
        }

        try (DirectoryStream<Path> stream = Files.newDirectoryStream(dir)) {
            for (Path path : stream) {
                if (!Files.isRegularFile(path)) continue;
                String name = path.getFileName().toString();
                if (name.toLowerCase().endsWith(".csv")) continue;

                Path target = dir.resolve(name + ".csv");
                try {
                    Files.move(path, target, StandardCopyOption.REPLACE_EXISTING);
                    log.info("Renamed file for task {}: {} -> {}", task.getId(), name, target.getFileName().toString());
                } catch (IOException ex) {
                    log.warn("Failed to rename file {} for task {}: {}", path, task.getId(), ex.getMessage(), ex);
                }
            }
        } catch (IOException ioe) {
            log.warn("Error scanning target directory {} for task {}: {}", targetPath, task.getId(), ioe.getMessage(), ioe);
        }
    }
}
