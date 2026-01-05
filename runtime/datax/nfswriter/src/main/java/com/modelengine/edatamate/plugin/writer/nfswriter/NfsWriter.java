package com.modelengine.edatamate.plugin.writer.nfswriter;

import com.alibaba.datax.common.element.Record;
import com.alibaba.datax.common.exception.CommonErrorCode;
import com.alibaba.datax.common.exception.DataXException;
import com.alibaba.datax.common.plugin.RecordReceiver;
import com.alibaba.datax.common.spi.Writer;
import com.alibaba.datax.common.util.Configuration;

import org.apache.commons.lang3.StringUtils;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

public class NfsWriter extends Writer {
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
            MountUtil.mount(this.jobConfig.getString("ip") + ":" + this.jobConfig.getString("path"),
                    mountPoint, "nfs", StringUtils.EMPTY);
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
                MountUtil.umount(this.mountPoint);
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
        private String destPath;
        private List<String> files;

        @Override
        public void init() {
            this.jobConfig = super.getPluginJobConf();
            this.destPath = this.jobConfig.getString("destPath");
            this.mountPoint = this.jobConfig.getString("mountPoint");
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

                    String filePath = this.mountPoint + "/" + fileName;
                    ShellUtil.runCommand("rsync", Arrays.asList("--no-links", "--chmod=754", "--", filePath,
                            this.destPath + "/" + fileName));
                }
            } catch (Exception e) {
                throw DataXException.asDataXException(CommonErrorCode.RUNTIME_ERROR, e);
            }
        }

        @Override
        public void destroy() {
        }
    }
}
