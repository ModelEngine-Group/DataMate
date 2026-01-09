package com.datamate.plugin.reader.localreader;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import com.alibaba.datax.common.element.Record;
import com.alibaba.datax.common.element.StringColumn;
import com.alibaba.datax.common.plugin.RecordSender;
import com.alibaba.datax.common.spi.Reader;
import com.alibaba.datax.common.util.Configuration;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * 本地文件夹读取器
 * 从本地文件系统的指定目录读取文件列表
 */
public class LocalReader extends Reader {

    private static final Logger LOG = LoggerFactory.getLogger(LocalReader.class);

    public static class Job extends Reader.Job {
        private Configuration jobConfig = null;

        @Override
        public void init() {
            this.jobConfig = super.getPluginJobConf();
        }

        @Override
        public void prepare() {
            String path = this.jobConfig.getString("path");
            if (path == null || path.isEmpty()) {
                throw new RuntimeException("path is required for localreader");
            }
            Path dirPath = Paths.get(path);
            if (!Files.exists(dirPath)) {
                throw new RuntimeException("path does not exist: " + path);
            }
            if (!Files.isDirectory(dirPath)) {
                throw new RuntimeException("path is not a directory: " + path);
            }
        }

        @Override
        public List<Configuration> split(int adviceNumber) {
            return Collections.singletonList(this.jobConfig);
        }

        @Override
        public void post() {
        }

        @Override
        public void destroy() {
        }
    }

    public static class Task extends Reader.Task {

        private Configuration jobConfig;
        private String path;
        private Set<String> fileType;
        private List<String> files;

        @Override
        public void init() {
            this.jobConfig = super.getPluginJobConf();
            this.path = this.jobConfig.getString("path");
            this.fileType = new HashSet<>(this.jobConfig.getList("fileType", Collections.emptyList(), String.class));
            this.files = this.jobConfig.getList("files", Collections.emptyList(), String.class);
        }

        @Override
        public void startRead(RecordSender recordSender) {
            try (Stream<Path> stream = Files.list(Paths.get(this.path))) {
                List<String> fileList = stream.filter(Files::isRegularFile)
                        .filter(file -> fileType.isEmpty() || fileType.contains(getFileSuffix(file)))
                        .map(p -> p.getFileName().toString())
                        .filter(fileName -> this.files.isEmpty() || this.files.contains(fileName))
                        .collect(Collectors.toList());
                fileList.forEach(filePath -> {
                    Record record = recordSender.createRecord();
                    record.addColumn(new StringColumn(filePath));
                    recordSender.sendToWriter(record);
                });
                this.jobConfig.set("columnNumber", 1);
            } catch (IOException e) {
                LOG.error("Error reading files from local path: {}", this.path, e);
                throw new RuntimeException(e);
            }
        }

        private String getFileSuffix(Path path) {
            String fileName = path.getFileName().toString();
            int lastDotIndex = fileName.lastIndexOf('.');
            if (lastDotIndex == -1 || lastDotIndex == fileName.length() - 1) {
                return "";
            }
            return fileName.substring(lastDotIndex + 1);
        }

        @Override
        public void destroy() {
        }
    }
}
