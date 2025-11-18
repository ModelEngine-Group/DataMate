// java
package com.datamate.plugin.writer.obswriter;

import java.io.IOException;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import com.alibaba.datax.common.element.Record;
import com.alibaba.datax.common.element.StringColumn;
import com.alibaba.datax.common.exception.CommonErrorCode;
import com.alibaba.datax.common.exception.DataXException;
import com.alibaba.datax.common.plugin.RecordReceiver;
import com.alibaba.datax.common.spi.Writer;
import com.alibaba.datax.common.util.Configuration;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.core.sync.ResponseTransformer;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.S3Configuration;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;

public class ObsWriter extends Writer {

    private static final Logger LOG = LoggerFactory.getLogger(ObsWriter.class);

    public static class Job extends Writer.Job {
        private Configuration jobConfig = null;

        @Override
        public void init() {
            this.jobConfig = super.getPluginJobConf();
        }

        @Override
        public void prepare() {
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

    public static class Task extends Writer.Task {

        private Configuration jobConfig;
        private Set<String> fileType;
        private String endpoint;
        private String accessKey;
        private String secretKey;
        private String bucket;
        private String destPath;
        private S3Client s3;

        @Override
        public void init() {
            this.jobConfig = super.getPluginJobConf();
            this.fileType = new HashSet<>(this.jobConfig.getList("fileType", Collections.emptyList(), String.class));
            this.endpoint = this.jobConfig.getString("endpoint");
            this.accessKey = this.jobConfig.getString("accessKey");
            this.secretKey = this.jobConfig.getString("secretKey");
            this.bucket = this.jobConfig.getString("bucket");
            this.destPath = this.jobConfig.getString("destPath");
            this.s3 = getS3Client();
        }

        private S3Client getS3Client() {
            try {
                AwsBasicCredentials creds = AwsBasicCredentials.create(accessKey, secretKey);
                S3Configuration serviceConfig = S3Configuration.builder()
                    .pathStyleAccessEnabled(true)
                    .build();
                return S3Client.builder()
                    .endpointOverride(new URI(endpoint))
                    .region(Region.of("us-east-1"))
                    .serviceConfiguration(serviceConfig)
                    .credentialsProvider(StaticCredentialsProvider.create(creds))
                    .build();
            } catch (Exception e) {
                LOG.error("Error init s3 client: {}", this.endpoint, e);
                throw DataXException.asDataXException(CommonErrorCode.RUNTIME_ERROR, e);
            }
        }

        @Override
        public void startWrite(RecordReceiver lineReceiver) {
            try {
                Record record;
                while ((record = lineReceiver.getFromReader()) != null) {
                    String key = record.getColumn(0).asString();
                    if (StringUtils.isBlank(key)) {
                        continue;
                    }
                    copyFileFromObs(key);
                }
            } catch (Exception e) {
                LOG.error("Error reading files from obs file system: {}", this.endpoint, e);
                throw DataXException.asDataXException(CommonErrorCode.RUNTIME_ERROR, e);
            }
        }

        private void copyFileFromObs(String key) throws IOException {
            if (StringUtils.isBlank(endpoint) || StringUtils.isBlank(bucket)) {
                throw new IllegalArgumentException("endpoint and bucket must be provided");
            }
            try {
                // 确保目标目录存在
                Path targetDir = Paths.get(destPath);
                try {
                    Files.createDirectories(targetDir);
                } catch (IOException e) {
                    LOG.warn("Create dest dir {} failed: {}", targetDir, e.getMessage(), e);
                }

                // 下载对象到本地目录，文件名取 key 最后一段
                String fileName = Paths.get(key).getFileName().toString();
                if (StringUtils.isBlank(fileName)) {
                    // 防护：无法解析文件名则跳过下载
                    LOG.warn("Skip object with empty file name for key {}", key);
                    return;
                }
                Path target = targetDir.resolve(fileName);
                try {
                    if (Files.exists(target)) {
                        Files.delete(target);
                    }
                    GetObjectRequest getReq = GetObjectRequest.builder()
                        .bucket(bucket)
                        .key(key)
                        .build();
                    s3.getObject(getReq, ResponseTransformer.toFile(target));
                    LOG.info("Downloaded obs object {} to {}", key, target.toString());
                } catch (Exception ex) {
                    LOG.warn("Failed to download object {}: {}", key, ex.getMessage(), ex);
                }
            } catch (Exception e) {
                LOG.warn("Failed to build S3 client or download object {}: {}", key, e.getMessage(), e);
                // 保持原行为，对下载失败记录 warn，但不抛出新的运行时错误（外层会捕获）
            }
        }

        @Override
        public void destroy() {
            if (s3 != null) {
                try {
                    s3.close();
                } catch (Exception ignore) {
                }
            }
        }
    }
}
