package com.datamate.collection.infrastructure.datax.config;

import com.datamate.collection.domain.model.entity.CollectionTask;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.Getter;
import lombok.Setter;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Getter
@Setter
public class NasConfig implements BaseConfig{
    private String ip;

    private String path;

    private List<String> files;

    /**
     * 将当前 NAS 配置构造成 DataX 所需的 job JSON 字符串。
     */
    public String toJobConfig(ObjectMapper objectMapper, CollectionTask task) throws Exception {
        Map<String, Object> parameter = new HashMap<>();
        if (ip != null) parameter.put("ip", ip);
        if (path != null) parameter.put("path", path);
        if (files != null) parameter.put("files", files);
        parameter.put("destPath", task.getTargetPath());

        Map<String, Object> job = new HashMap<>();
        Map<String, Object> content = new HashMap<>();
        Map<String, Object> reader = new HashMap<>();
        reader.put("name", "nfsreader");
        reader.put("parameter", parameter);
        content.put("reader", reader);

        Map<String, Object> writer = new HashMap<>();
        writer.put("name", "nfswriter");
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
