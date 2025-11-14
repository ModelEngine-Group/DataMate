package com.datamate.plugin.reader.obsreader;

import java.io.IOException;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
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
import software.amazon.awssdk.core.sync.ResponseTransformer;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.ListObjectsV2Request;
import software.amazon.awssdk.services.s3.model.ListObjectsV2Response;
import software.amazon.awssdk.services.s3.model.S3Object;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.S3Configuration;

public class ObsReader extends Reader {

    private static final Logger LOG = LoggerFactory.getLogger(ObsReader.class);

    public static class Job extends Reader.Job {
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

    public static class Task extends Reader.Task {

        private Configuration jobConfig;
        private Set<String> fileType;
        private String endpoint;
        private String accessKey;
        private String secretKey;
        private String bucket;
        private String prefix;
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
                LOG.error("Error reading files from obs file system: {}", this.endpoint, e);
                throw new RuntimeException(e);
            }
        }

        /**
         * 使用 AWS SDK v2 列举 S3/OBS 对象并将对象下载到 /dataset/local/。
         * 非递归：只列举 prefix 当前目录下的对象（通过 delimiter="/" 实现）。
         * 返回对象 key 列表（下载后文件名为 key 的最后一段）。
         */
        private List<String> listFiles() throws Exception {
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
                        .delimiter("/"); // 非递归：只列出当前目录下的对象（不下钻子目录）
                    if (continuationToken != null) reqBuilder.continuationToken(continuationToken);
                    ListObjectsV2Response res = s3.listObjectsV2(reqBuilder.build());
                    for (S3Object obj : res.contents()) {
                        String key = obj.key();
                        if (isInValid(key)) continue;
                        // 到此认为是“文件”key（且位于 prefix 当前目录）
                        keys.add(key);
                    }
                    continuationToken = res.isTruncated() ? res.nextContinuationToken() : null;
                } while (continuationToken != null);
            } catch (Exception e) {
                LOG.warn("Failed to build S3 client or read object: {}", e.getMessage(), e);
                // 保持原行为，对下载失败记录 warn，但不抛出新的运行时错误（外层会捕获）
            }
            return keys;
        }

        private boolean isInValid(String key) {
            // 仅接受以 effectivePrefix 开头的 key（请求通常已保证），并排除目录占位符
            if (!effectivePrefix.isEmpty() && !key.startsWith(effectivePrefix)) {
                return true;
            }
            if (key.equals(effectivePrefix) || key.endsWith("/")) {
                // 这是一个目录占位符或与 prefix 相同，跳过
                return true;
            }
            return false;
        }

        private String getEffectivePrefix() {
            // 规范化 prefix：去掉前导 '/'，并确保以 '/' 结尾以表示目录前缀（如果非空）
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
                    .region(Region.of("us-east-1"))
                    .serviceConfiguration(serviceConfig)
                    .credentialsProvider(StaticCredentialsProvider.create(creds))
                    .build();
            } catch (Exception e) {
                LOG.error("Error init s3 client: {}", this.endpoint, e);
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
