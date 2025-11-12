package com.datamate.collection.infrastructure.datax.config;

import com.datamate.collection.domain.model.entity.CollectionTask;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.Getter;
import lombok.Setter;
import org.apache.commons.collections4.CollectionUtils;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Getter
@Setter
public class MysqlConfig {
    private String jdbcUrl;

    private  String username;

    private String password;

    private String querySql;

    private List<String> headers;

    /**
     * 将当前 MYSQL 配置构造成 DataX 所需的 job JSON 字符串。
     */
    public String toJobConfig(ObjectMapper objectMapper, CollectionTask task) throws Exception {
        Map<String, Object> mysqlParameter = new HashMap<>();
        Map<String, Object> connection = new HashMap<>();
        if (username != null) mysqlParameter.put("username", username);
        if (password != null) mysqlParameter.put("password", password);
        if (jdbcUrl != null) connection.put("jdbcUrl", Collections.singletonList(jdbcUrl));
        if (querySql != null) connection.put("querySql", Collections.singletonList(querySql));
        mysqlParameter.put("connection", Collections.singletonList(connection));

        Map<String, Object> job = new HashMap<>();
        Map<String, Object> content = new HashMap<>();
        Map<String, Object> reader = new HashMap<>();
        reader.put("name", "mysqlreader");
        reader.put("parameter", mysqlParameter);
        content.put("reader", reader);

        Map<String, Object> writer = new HashMap<>();
        Map<String, Object> writerParameter = new HashMap<>();
        writer.put("name", "txtfilewriter");
        if (CollectionUtils.isNotEmpty(headers)) {
            writerParameter.put("header", headers);
        }
        writerParameter.put("path", task.getTargetPath());
        writerParameter.put("fileName", "collectionResult");
        writerParameter.put("writeMode", "truncate");
        writerParameter.put("dateFormat", "yyyy-MM-dd HH:mm:ss");
        writerParameter.put("fileFormat", "csv");
        writerParameter.put("encoding", "UTF-8");
        writerParameter.put("fieldDelimiter", ",");
        writer.put("parameter", writerParameter);
        content.put("writer", writer);

        job.put("content", List.of(content));
        Map<String, Object> setting = new HashMap<>();
        Map<String, Object> channel = new HashMap<>();
        channel.put("channel", 1);
        setting.put("speed", channel);
        job.put("setting", setting);

        Map<String, Object> jobConfig = new HashMap<>();
        jobConfig.put("job", job);
        return objectMapper.writeValueAsString(jobConfig);
    }
}
