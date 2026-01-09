package com.datamate.plugin.reader.glusterfsreader;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import com.alibaba.datax.common.element.Record;
import com.alibaba.datax.common.element.StringColumn;
import com.alibaba.datax.common.plugin.RecordSender;
import com.alibaba.datax.common.spi.Reader;
import com.alibaba.datax.common.util.Configuration;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * GlusterFS Reader 插件
 * 通过 mount -t glusterfs 挂载 GlusterFS 卷，读取文件列表
 */
public class GlusterfsReader extends Reader {

    private static final Logger LOG = LoggerFactory.getLogger(GlusterfsReader.class);

    public static class Job extends Reader.Job {
        private Configuration jobConfig = null;
        private String mountPoint;

        @Override
        public void init() {
            this.jobConfig = super.getPluginJobConf();
        }

        @Override
        public void prepare() {
            this.mountPoint = "/dataset/mount/" + UUID.randomUUID();
            this.jobConfig.set("mountPoint", this.mountPoint);

            String ip = this.jobConfig.getString("ip");
            String volume = this.jobConfig.getString("volume");
            String subPath = this.jobConfig.getString("path", "");

            // GlusterFS mount 格式: mount -t glusterfs ip:/volume /mountpoint
            String remote = ip + ":/" + volume;
            GlusterfsMountUtil.mount(remote, mountPoint, subPath);
        }

        @Override
        public List<Configuration> split(int adviceNumber) {
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

    public static class Task extends Reader.Task {

        private Configuration jobConfig;
        private String mountPoint;
        private String subPath;
        private Set<String> fileType;
        private List<String> files;

        @Override
        public void init() {
            this.jobConfig = super.getPluginJobConf();
            this.mountPoint = this.jobConfig.getString("mountPoint");
            this.subPath = this.jobConfig.getString("path", "");
            this.fileType = new HashSet<>(this.jobConfig.getList("fileType", Collections.emptyList(), String.class));
            this.files = this.jobConfig.getList("files", Collections.emptyList(), String.class);
        }

        @Override
        public void startRead(RecordSender recordSender) {
            String readPath = this.mountPoint;
            if (StringUtils.isNotBlank(this.subPath)) {
                readPath = this.mountPoint + "/" + this.subPath.replaceFirst("^/+", "");
            }

            try (Stream<Path> stream = Files.list(Paths.get(readPath))) {
                List<String> fileList = stream.filter(Files::isRegularFile)
                        .filter(file -> fileType.isEmpty() || fileType.contains(getFileSuffix(file)))
                        .map(path -> path.getFileName().toString())
                        .filter(fileName -> this.files.isEmpty() || this.files.contains(fileName))
                        .collect(Collectors.toList());

                fileList.forEach(filePath -> {
                    Record record = recordSender.createRecord();
                    record.addColumn(new StringColumn(filePath));
                    recordSender.sendToWriter(record);
                });
                this.jobConfig.set("columnNumber", 1);
            } catch (IOException e) {
                LOG.error("Error reading files from GlusterFS mount point: {}", readPath, e);
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
