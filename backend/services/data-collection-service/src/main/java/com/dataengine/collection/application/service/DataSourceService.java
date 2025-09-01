package com.dataengine.collection.application.service;

import com.dataengine.collection.domain.model.DataSource;
import com.dataengine.collection.domain.model.DataSourceStatus;
import com.dataengine.collection.infrastructure.persistence.mapper.DataSourceMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class DataSourceService {
    private final DataSourceMapper dataSourceMapper;

    @Transactional
    public DataSource create(DataSource ds) {
        ds.setId(UUID.randomUUID().toString());
        ds.setStatus(DataSourceStatus.ACTIVE);
        ds.setCreatedAt(LocalDateTime.now());
        ds.setUpdatedAt(LocalDateTime.now());
        dataSourceMapper.insert(ds);
        return ds;
    }

    @Transactional
    public DataSource update(DataSource ds) {
        ds.setUpdatedAt(LocalDateTime.now());
        dataSourceMapper.update(ds);
        return ds;
    }

    @Transactional
    public void delete(String id) {
        dataSourceMapper.deleteById(id);
    }

    public DataSource get(String id) { return dataSourceMapper.selectById(id); }

    public List<DataSource> list(Integer page, Integer size, String type, String status, String name) {
        Map<String, Object> p = new HashMap<>();
        p.put("type", type);
        p.put("status", status);
        p.put("name", name);
        if (page != null && size != null) {
            p.put("offset", page * size);
            p.put("limit", size);
        }
        return dataSourceMapper.selectAll(p);
    }

    public long count(String type, String status, String name) {
        Map<String, Object> p = new HashMap<>();
        p.put("type", type);
        p.put("status", status);
        p.put("name", name);
        return dataSourceMapper.count(p);
    }

    @Transactional
    public void updateTestResult(String id, boolean success, String message, long latencyMs) {
        String resultJson = String.format("{\"success\":%s,\"message\":%s,\"latency\":%d}", success,
                message == null ? "null" : ("\"" + message.replace("\"","\\\"") + "\""), latencyMs);
        dataSourceMapper.updateTestResult(id, LocalDateTime.now(), resultJson);
    }
}
