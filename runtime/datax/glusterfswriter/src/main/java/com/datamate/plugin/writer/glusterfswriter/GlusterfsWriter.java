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
            new File(destPath).mkdirs();
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
        }

        @Override
        public void startWrite(RecordReceiver lineReceiver) {
            String sourcePath = this.mountPoint;
            if (StringUtils.isNotBlank(this.subPath)) {
                sourcePath = this.mountPoint + "/" + this.subPath.replaceFirst("^/+", "");
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

                    String filePath = sourcePath + "/" + fileName;
                    ShellUtil.runCommand("rsync", Arrays.asList("--no-links", "--chmod=754", "--", filePath,
                            this.destPath + "/" + fileName));
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
