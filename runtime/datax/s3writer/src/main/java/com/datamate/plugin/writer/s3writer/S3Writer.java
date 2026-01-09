package com.datamate.plugin.writer.s3writer;

import java.io.IOException;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import com.alibaba.datax.common.element.Record;
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

/**
 * S3兼容对象存储写入器
 * 从S3兼容存储下载文件到本地目标目录
 */
public class S3Writer extends Writer {

    private static final Logger LOG = LoggerFactory.getLogger(S3Writer.class);

    public static class Job extends Writer.Job {
        private Configuration jobConfig = null;

        @Override
        public void init() {
            this.jobConfig = super.getPluginJobConf();
        }

        @Override
        public void prepare() {
            String destPath = this.jobConfig.getString("destPath");
            if (StringUtils.isBlank(destPath)) {
                throw new RuntimeException("destPath is required for s3writer");
            }
            try {
                Files.createDirectories(Paths.get(destPath));
            } catch (IOException e) {
                throw new RuntimeException("Failed to create destination directory: " + destPath, e);
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

    public static class Task extends Writer.Task {

        private Configuration jobConfig;
        private Set<String> fileType;
        private String endpoint;
        private String accessKey;
        private String secretKey;
        private String bucket;
        private String destPath;
        private String region;
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
            this.region = this.jobConfig.getString("region", "us-east-1");
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
                    .region(Region.of(region))
                    .serviceConfiguration(serviceConfig)
                    .credentialsProvider(StaticCredentialsProvider.create(creds))
                    .build();
            } catch (Exception e) {
                LOG.error("Error init S3 client: {}", this.endpoint, e);
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
                    copyFileFromS3(key);
                }
            } catch (Exception e) {
                LOG.error("Error writing files from S3 compatible storage: {}", this.endpoint, e);
                throw DataXException.asDataXException(CommonErrorCode.RUNTIME_ERROR, e);
            }
        }

        private void copyFileFromS3(String key) throws IOException {
            if (StringUtils.isBlank(endpoint) || StringUtils.isBlank(bucket)) {
                throw new IllegalArgumentException("endpoint and bucket must be provided");
            }
            try {
                Path targetDir = Paths.get(destPath);
                try {
                    Files.createDirectories(targetDir);
                } catch (IOException e) {
                    LOG.warn("Create dest dir {} failed: {}", targetDir, e.getMessage(), e);
                }

                String fileName = Paths.get(key).getFileName().toString();
                if (StringUtils.isBlank(fileName)) {
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
                    LOG.info("Downloaded S3 object {} to {}", key, target.toString());
                } catch (Exception ex) {
                    LOG.warn("Failed to download object {}: {}", key, ex.getMessage(), ex);
                }
            } catch (Exception e) {
                LOG.warn("Failed to download object {}: {}", key, e.getMessage(), e);
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
