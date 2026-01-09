package com.datamate.plugin.writer.localwriter;

import com.alibaba.datax.common.element.Record;
import com.alibaba.datax.common.exception.CommonErrorCode;
import com.alibaba.datax.common.exception.DataXException;
import com.alibaba.datax.common.plugin.RecordReceiver;
import com.alibaba.datax.common.spi.Writer;
import com.alibaba.datax.common.util.Configuration;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.Collections;
import java.util.List;

/**
 * 本地文件夹写入器
 * 从本地源目录复制文件到目标目录
 */
public class LocalWriter extends Writer {

    private static final Logger LOG = LoggerFactory.getLogger(LocalWriter.class);

    public static class Job extends Writer.Job {
        private Configuration jobConfig;

        @Override
        public void init() {
            this.jobConfig = super.getPluginJobConf();
        }

        @Override
        public void prepare() {
            String destPath = this.jobConfig.getString("destPath");
            if (destPath == null || destPath.isEmpty()) {
                throw new RuntimeException("destPath is required for localwriter");
            }
            try {
                Files.createDirectories(Paths.get(destPath));
            } catch (IOException e) {
                throw new RuntimeException("Failed to create destination directory: " + destPath, e);
            }
        }

        @Override
        public List<Configuration> split(int mandatoryNumber) {
            return Collections.singletonList(this.jobConfig);
        }

        @Override
        public void post() {
        }

        @Override
        public void destroy() {
        }
    }

    public static class Task extends Writer.Task {
        private Configuration jobConfig;
        private String sourcePath;
        private String destPath;
        private List<String> files;

        @Override
        public void init() {
            this.jobConfig = super.getPluginJobConf();
            this.sourcePath = this.jobConfig.getString("path");
            this.destPath = this.jobConfig.getString("destPath");
            this.files = this.jobConfig.getList("files", Collections.emptyList(), String.class);
        }

        @Override
        public void startWrite(RecordReceiver lineReceiver) {
            try {
                Record record;
                while ((record = lineReceiver.getFromReader()) != null) {
                    String fileName = record.getColumn(0).asString();
                    if (StringUtils.isBlank(fileName)) {
                        continue;
                    }
                    if (!files.isEmpty() && !files.contains(fileName)) {
                        continue;
                    }
                    copyFile(fileName);
                }
            } catch (Exception e) {
                throw DataXException.asDataXException(CommonErrorCode.RUNTIME_ERROR, e);
            }
        }

        private void copyFile(String fileName) {
            Path source = Paths.get(this.sourcePath, fileName);
            Path target = Paths.get(this.destPath, fileName);
            try {
                if (!Files.exists(source)) {
                    LOG.warn("Source file does not exist: {}", source);
                    return;
                }
                Files.copy(source, target, StandardCopyOption.REPLACE_EXISTING);
                LOG.info("Copied file {} to {}", source, target);
            } catch (IOException e) {
                LOG.error("Failed to copy file {} to {}: {}", source, target, e.getMessage(), e);
                throw new RuntimeException("Failed to copy file: " + fileName, e);
            }
        }

        @Override
        public void destroy() {
        }
    }
}
