package com.datamate.plugin.writer.glusterfswriter;

import com.alibaba.datax.common.element.Record;
import com.alibaba.datax.common.exception.CommonErrorCode;
import com.alibaba.datax.common.exception.DataXException;
import com.alibaba.datax.common.plugin.RecordReceiver;
import com.alibaba.datax.common.spi.Writer;
import com.alibaba.datax.common.util.Configuration;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

/**
 * GlusterFS Writer 插件
 * 通过 mount -t glusterfs 挂载 GlusterFS 卷，将文件写入到目标位置
 */
public class GlusterfsWriter extends Writer {

    private static final Logger LOG = LoggerFactory.getLogger(GlusterfsWriter.class);

    /** 允许的目标路径基础目录 */
    private static final String ALLOWED_DEST_BASE = "/dataset";

    public static class Job extends Writer.Job {
        private Configuration jobConfig;
        private String mountPoint;

        @Override
        public void init() {
            this.jobConfig = super.getPluginJobConf();
        }

        @Override
        public void prepare() {
            this.mountPoint = "/dataset/mount/" + UUID.randomUUID();
            this.jobConfig.set("mountPoint", this.mountPoint);
            new File(this.mountPoint).mkdirs();

            String ip = this.jobConfig.getString("ip");
            String volume = this.jobConfig.getString("volume");

            // GlusterFS mount 格式: mount -t glusterfs ip:/volume /mountpoint
            String remote = ip + ":/" + volume;
            GlusterfsMountUtil.mount(remote, mountPoint);

            String destPath = this.jobConfig.getString("destPath");
            // 防止路径穿越：规范化后校验目标路径在允许目录内
            Path normalizedDest = Paths.get(destPath).normalize().toAbsolutePath();
            if (!normalizedDest.startsWith(ALLOWED_DEST_BASE)) {
                throw new IllegalArgumentException(
                    "destPath is outside allowed directory: " + destPath);
            }
            new File(normalizedDest.toString()).mkdirs();
        }

        @Override
        public List<Configuration> split(int mandatoryNumber) {
            return Collections.singletonList(this.jobConfig);
        }

        @Override
        public void post() {
            try {
                GlusterfsMountUtil.umount(this.mountPoint);
                new File(this.mountPoint).deleteOnExit();
            } catch (IOException | InterruptedException e) {
                throw new RuntimeException(e);
            }
        }

        @Override
        public void destroy() {
        }
    }

    public static class Task extends Writer.Task {
        private Configuration jobConfig;
        private String mountPoint;
        private String subPath;
        private String destPath;
        private List<String> files;

        @Override
        public void init() {
            this.jobConfig = super.getPluginJobConf();
            this.destPath = this.jobConfig.getString("destPath");
            this.mountPoint = this.jobConfig.getString("mountPoint");
            this.subPath = this.jobConfig.getString("path", "");
            this.files = this.jobConfig.getList("files", Collections.emptyList(), String.class);

            // 防止路径穿越：subPath 不能包含 ..
            if (StringUtils.isNotBlank(this.subPath) && this.subPath.contains("..")) {
                throw new IllegalArgumentException(
                    "Invalid subPath (path traversal): " + this.subPath);
            }
        }

        @Override
        public void startWrite(RecordReceiver lineReceiver) {
            String sourcePath = this.mountPoint;
            if (StringUtils.isNotBlank(this.subPath)) {
                sourcePath = this.mountPoint + "/" + this.subPath.replaceFirst("^/+", "");
            }

            // 防止路径穿越：规范化后校验源路径仍在 mount 点下
            Path normalizedSourcePath = Paths.get(sourcePath).normalize().toAbsolutePath();
            Path normalizedMount = Paths.get(this.mountPoint).normalize().toAbsolutePath();
            if (!normalizedSourcePath.startsWith(normalizedMount)) {
                LOG.error("Path traversal detected: sourcePath={} outside mountPoint={}",
                    normalizedSourcePath, normalizedMount);
                throw DataXException.asDataXException(CommonErrorCode.RUNTIME_ERROR,
                    "Source path outside mount point: " + sourcePath);
            }

            // 防止路径穿越：校验目标路径在允许目录内
            Path normalizedDest = Paths.get(this.destPath).normalize().toAbsolutePath();
            if (!normalizedDest.startsWith(ALLOWED_DEST_BASE)) {
                throw DataXException.asDataXException(CommonErrorCode.RUNTIME_ERROR,
                    "destPath outside allowed directory: " + this.destPath);
            }

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

                    // 防止路径穿越：fileName 不能包含路径分隔符或 ..
                    if (fileName.contains("..") || fileName.contains("/") || fileName.contains("\\")) {
                        LOG.warn("Skipping file with suspicious name: {}", fileName);
                        continue;
                    }

                    String filePath = normalizedSourcePath + "/" + fileName;
                    ShellUtil.runCommand("rsync", Arrays.asList("--no-links", "--chmod=754", "--", filePath,
                            normalizedDest + "/" + fileName));
                }
            } catch (Exception e) {
                LOG.error("Error writing files from GlusterFS: {}", e.getMessage(), e);
                throw DataXException.asDataXException(CommonErrorCode.RUNTIME_ERROR, e);
            }
        }

        @Override
        public void destroy() {
        }
    }
}
