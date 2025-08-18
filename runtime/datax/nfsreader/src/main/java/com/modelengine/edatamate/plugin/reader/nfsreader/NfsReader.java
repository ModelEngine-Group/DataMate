package com.modelengine.edatamate.plugin.reader.nfsreader;

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

public class NfsReader extends Reader {

    private static final Logger LOG = LoggerFactory.getLogger(NfsReader.class);

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
            MountUtil.mount(this.jobConfig.getString("ip") + ":" + this.jobConfig.getString("path"),
                    mountPoint, "nfs", StringUtils.EMPTY);
        }

        @Override
        public List<Configuration> split(int adviceNumber) {
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

    public static class Task extends Reader.Task {

        private Configuration jobConfig;
        private String mountPoint;
        private Set<String> fileType;

        @Override
        public void init() {
            this.jobConfig = super.getPluginJobConf();
            this.mountPoint = this.jobConfig.getString("mountPoint");
            this.fileType = new HashSet<>(this.jobConfig.getList("fileType", Collections.emptyList(), String.class));
        }

        @Override
        public void startRead(RecordSender recordSender) {
            try (Stream<Path> stream = Files.list(Paths.get(this.mountPoint))) {
                List<String> files = stream.filter(Files::isRegularFile)
                        .filter(file -> fileType.isEmpty() || fileType.contains(getFileSuffix(file)))
                        .map(path -> path.getFileName().toString())
                        .collect(Collectors.toList());
                files.forEach(filePath -> {
                    Record record = recordSender.createRecord();
                    record.addColumn(new StringColumn(filePath));
                    recordSender.sendToWriter(record);
                });
                this.jobConfig.set("columnNumber", 1);
            } catch (IOException e) {
                LOG.error("Error reading files from mount point: {}", this.mountPoint, e);
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
