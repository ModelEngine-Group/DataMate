package com.datamate.plugin.reader.s3reader;

import java.net.URI;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

import com.alibaba.datax.common.element.Record;
import com.alibaba.datax.common.element.StringColumn;
import com.alibaba.datax.common.exception.CommonErrorCode;
import com.alibaba.datax.common.exception.DataXException;
import com.alibaba.datax.common.plugin.RecordSender;
import com.alibaba.datax.common.spi.Reader;
import com.alibaba.datax.common.util.Configuration;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.ListObjectsV2Request;
import software.amazon.awssdk.services.s3.model.ListObjectsV2Response;
import software.amazon.awssdk.services.s3.model.S3Object;
import software.amazon.awssdk.services.s3.S3Configuration;

/**
 * S3兼容对象存储读取器
 * 支持自定义 S3 兼容对象存储（如 MinIO、Ceph 等）
 */
public class S3Reader extends Reader {

    private static final Logger LOG = LoggerFactory.getLogger(S3Reader.class);

    public static class Job extends Reader.Job {
        private Configuration jobConfig = null;

        @Override
        public void init() {
            this.jobConfig = super.getPluginJobConf();
        }

        @Override
        public void prepare() {
            String endpoint = this.jobConfig.getString("endpoint");
            String bucket = this.jobConfig.getString("bucket");
            String accessKey = this.jobConfig.getString("accessKey");
            String secretKey = this.jobConfig.getString("secretKey");

            if (StringUtils.isBlank(endpoint)) {
                throw new RuntimeException("endpoint is required for s3reader");
            }
            if (StringUtils.isBlank(bucket)) {
                throw new RuntimeException("bucket is required for s3reader");
            }
            if (StringUtils.isBlank(accessKey)) {
                throw new RuntimeException("accessKey is required for s3reader");
            }
            if (StringUtils.isBlank(secretKey)) {
                throw new RuntimeException("secretKey is required for s3reader");
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
        private Set<String> fileType;
        private String endpoint;
        private String accessKey;
        private String secretKey;
        private String bucket;
        private String prefix;
        private String region;
        private S3Client s3;
        private String effectivePrefix;

        @Override
        public void init() {
            this.jobConfig = super.getPluginJobConf();
            this.fileType = new HashSet<>(this.jobConfig.getList("fileType", Collections.emptyList(), String.class));
            this.endpoint = this.jobConfig.getString("endpoint");
            this.accessKey = this.jobConfig.getString("accessKey");
            this.secretKey = this.jobConfig.getString("secretKey");
            this.bucket = this.jobConfig.getString("bucket");
            this.prefix = this.jobConfig.getString("prefix");
            // OBS也是默认us-east-1，这里保留默认值
            this.region = this.jobConfig.getString("region", "us-east-1");
            this.s3 = getS3Client();
            this.effectivePrefix = getEffectivePrefix();
        }

        @Override
        public void startRead(RecordSender recordSender) {
            try {
                List<String> files = listFiles().stream()
                    .filter(file -> fileType.isEmpty() || fileType.contains(getFileSuffix(file)))
                    .collect(Collectors.toList());
                files.forEach(filePath -> {
                    Record record = recordSender.createRecord();
                    record.addColumn(new StringColumn(filePath));
                    recordSender.sendToWriter(record);
                });
                this.jobConfig.set("columnNumber", 1);
            } catch (Exception e) {
                LOG.error("Error reading files from S3 compatible storage: {}", this.endpoint, e);
                throw new RuntimeException(e);
            }
        }

        /**
         * 列举 S3 对象
         * 非递归：只列举 prefix 当前目录下的对象（通过 delimiter="/" 实现）
         */
        private List<String> listFiles() {
            if (StringUtils.isBlank(endpoint) || StringUtils.isBlank(bucket)) {
                throw new IllegalArgumentException("endpoint and bucket must be provided");
            }
            List<String> keys = new ArrayList<>();
            String continuationToken = null;
            try {
                do {
                    ListObjectsV2Request.Builder reqBuilder = ListObjectsV2Request.builder()
                        .bucket(bucket)
                        .prefix(effectivePrefix)
                        .delimiter("/");
                    if (continuationToken != null) {
                        reqBuilder.continuationToken(continuationToken);
                    }
                    ListObjectsV2Response res = s3.listObjectsV2(reqBuilder.build());
                    for (S3Object obj : res.contents()) {
                        String key = obj.key();
                        if (isInValid(key)) {
                            continue;
                        }
                        keys.add(key);
                    }
                    continuationToken = res.isTruncated() ? res.nextContinuationToken() : null;
                } while (continuationToken != null);
            } catch (Exception e) {
                LOG.warn("Failed to list S3 objects: {}", e.getMessage(), e);
            }
            return keys;
        }

        private boolean isInValid(String key) {
            if (!effectivePrefix.isEmpty() && !key.startsWith(effectivePrefix)) {
                return true;
            }
            if (key.equals(effectivePrefix) || key.endsWith("/")) {
                return true;
            }
            return false;
        }

        private String getEffectivePrefix() {
            String effectivePrefix = "";
            if (prefix != null) {
                effectivePrefix = prefix.startsWith("/") ? prefix.substring(1) : prefix;
                if (!effectivePrefix.isEmpty() && !effectivePrefix.endsWith("/")) {
                    effectivePrefix = effectivePrefix + "/";
                }
            }
            return effectivePrefix;
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

        private String getFileSuffix(String key) {
            String fileName = Paths.get(key).getFileName().toString();
            int lastDotIndex = fileName.lastIndexOf('.');
            if (lastDotIndex == -1 || lastDotIndex == fileName.length() - 1) {
                return "";
            }
            return fileName.substring(lastDotIndex + 1);
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
