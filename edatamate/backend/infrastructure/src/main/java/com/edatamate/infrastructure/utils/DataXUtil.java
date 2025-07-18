package com.edatamate.infrastructure.utils;


import com.alibaba.fastjson2.JSON;
import com.edatamate.common.datax.dto.DBParameter;
import com.edatamate.common.datax.dto.JobEnum;
import com.edatamate.common.datax.dto.Parameter;
import com.edatamate.common.datax.dto.Reader;
import com.edatamate.common.datax.dto.Writer;

import java.util.List;
import java.util.Map;
import java.util.Set;

public class DataXUtil {
    private final static String READER = "reader";

    private final static String WRITER = "writer";

    private final static Set<JobEnum> DB_JOB = Set.of(JobEnum.MYSQL, JobEnum.PGSQL);

    public static Reader generateReader(String config, JobEnum type) {
        if (DB_JOB.contains(type)) {
            return generateDBReader(config, type);
        }
        Parameter param = JSON.parseObject(config, type.getParameter());
        return Reader.builder()
                .name(type.getType() + READER)
                .parameter(param)
                .build();
    }

    public static Writer generateWriter(String config, JobEnum type) {
        if (DB_JOB.contains(type)) {
            return generateDBWriter(config, type);
        }
        Parameter param = JSON.parseObject(config, type.getParameter());
        return Writer.builder()
                .name(type.getType() + WRITER)
                .parameter(param)
                .build();
    }

    public static Reader generateDBReader(String config, JobEnum type) {
        DBParameter param = (DBParameter) JSON.parseObject(config, type.getParameter());
        List<Map<String, Object>> connection = List.of(Map.of("jdbcUrl", List.of(param.getJdbcUrl()),
                "table", List.of(param.getTable())));
        param.setConnection(connection);
        return Reader.builder()
                .name(type.getType() + READER)
                .parameter(param)
                .build();
    }

    public static Writer generateDBWriter(String config, JobEnum type) {
        DBParameter param = (DBParameter) JSON.parseObject(config, type.getParameter());
        List<Map<String, Object>> connection = List.of(Map.of("jdbcUrl", param.getJdbcUrl(),
                "table", List.of(param.getTable())));
        param.setConnection(connection);
        return Writer.builder()
                .name(type.getType() + WRITER)
                .parameter(param)
                .build();
    }
}
