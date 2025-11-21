package com.datamate.collection.infrastructure.datax.config;

import com.datamate.collection.domain.model.entity.CollectionTask;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.Getter;
import lombok.Setter;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * OBS 归集配置类
 *
 * @since 2025/11/18
 */
@Getter
@Setter
public class ObsConfig implements  BaseConfig{
    private String endpoint;
    private String bucket;
    private String accessKey;
    private String secretKey;
    private String prefix;

    /**
     * 将当前 OBS 配置构造成 DataX 所需的 job JSON 字符串。
     */
    public String toJobConfig(ObjectMapper objectMapper, CollectionTask task) throws Exception {
        Map<String, Object> parameter = new HashMap<>();
        if (endpoint != null) parameter.put("endpoint", endpoint);
        if (bucket != null) parameter.put("bucket", bucket);
        if (accessKey != null) parameter.put("accessKey", accessKey);
        if (secretKey != null) parameter.put("secretKey", secretKey);
        if (prefix != null) parameter.put("prefix", prefix);
        parameter.put("destPath", task.getTargetPath());

        Map<String, Object> job = new HashMap<>();
        Map<String, Object> content = new HashMap<>();
        Map<String, Object> reader = new HashMap<>();
        reader.put("name", "obsreader");
        reader.put("parameter", parameter);
        content.put("reader", reader);

        Map<String, Object> writer = new HashMap<>();
        writer.put("name", "obswriter");
        writer.put("parameter", parameter);
        content.put("writer", writer);

        job.put("content", List.of(content));
        Map<String, Object> setting = new HashMap<>();
        Map<String, Object> channel = new HashMap<>();
        channel.put("channel", 2);
        setting.put("speed", channel);
        job.put("setting", setting);

        Map<String, Object> jobConfig = new HashMap<>();
        jobConfig.put("job", job);
        return objectMapper.writeValueAsString(jobConfig);
    }
}
