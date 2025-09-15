package com.dataengine.collection.interfaces.facade;

import com.dataengine.collection.application.service.DataSourceService;
import com.dataengine.collection.domain.model.DataSource;
import com.dataengine.collection.interfaces.api.DataSourceApi;
import com.dataengine.collection.interfaces.dto.*;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequiredArgsConstructor
@Validated
@Slf4j
public class DataSourceController implements DataSourceApi {

    private final DataSourceService dataSourceService;
    private final ObjectMapper objectMapper;

    private DataSourceResponse toResponse(DataSource ds) {
        if (ds == null) {
            return null;
        }

        DataSourceResponse r = new DataSourceResponse();
        r.setId(ds.getId());
        r.setName(ds.getName());
        r.setDescription(ds.getDescription());

        // 安全处理枚举转换
        if (ds.getType() != null) {
            try {
                r.setType(DataSourceType.fromValue(ds.getType().name()));
            } catch (Exception e) {
                log.error("Failed to convert data source type: {} for datasource id: {}, error: {}",
                         ds.getType(), ds.getId(), e.getMessage());
                // 设置一个默认值或者抛出异常
                r.setType(DataSourceType.MYSQL);
            }
        }

        if (ds.getStatus() != null) {
            try {
                r.setStatus(DataSourceResponse.StatusEnum.fromValue(ds.getStatus().name()));
            } catch (Exception e) {
                log.error("Failed to convert data source status: {} for datasource id: {}, error: {}",
                         ds.getStatus(), ds.getId(), e.getMessage());
                r.setStatus(DataSourceResponse.StatusEnum.ACTIVE);
            }
        }

        r.setConfig(parseConfigJson(ds.getConfig()));
        return r;
    }

    private Map<String, Object> parseConfigJson(String configJson) {
        if (configJson == null || configJson.trim().isEmpty()) {
            return Map.of();
        }

        String trimmedJson = configJson.trim();
        if (trimmedJson.equals("{}")) {
            return Map.of();
        }

        try {
            return objectMapper.readValue(trimmedJson, new TypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            // 记录详细的错误信息用于调试
            log.warn("Failed to parse config JSON: {}, error: {}", trimmedJson, e.getMessage());
            // 返回包含错误信息的Map，便于前端处理
            return Map.of(
                "error", "Invalid JSON format",
                "message", e.getMessage(),
                "raw", trimmedJson
            );
        }
    }

    @Override
    public ResponseEntity<PagedDataSources> datasourcesGet(Integer page, Integer size, DataSourceType type, String status) {
        List<DataSource> list = dataSourceService.list(page, size,
                type == null ? null : type.getValue(), status, null);
        long total = dataSourceService.count(type == null ? null : type.getValue(), status, null);
        PagedDataSources p = new PagedDataSources();
        p.setContent(list.stream().map(this::toResponse).collect(Collectors.toList()));
        p.setNumber(page);
        p.setSize(size);
        p.setTotalElements(total);
        p.setTotalPages(size == null || size == 0 ? 1 : (int) Math.ceil(total * 1.0 / size));
        p.setFirst(page != null && page == 0);
        p.setLast(page != null && size != null && (page + 1) * size >= total);
        return ResponseEntity.ok(p);
    }

    @Override
    public ResponseEntity<Void> datasourcesIdDelete(String id) {
        dataSourceService.delete(id);
        return ResponseEntity.noContent().build();
    }

    @Override
    public ResponseEntity<DataSourceResponse> datasourcesIdGet(String id) {
        log.debug("Getting data source by id: {}", id);
        DataSource ds = dataSourceService.get(id);
        return ds == null ? ResponseEntity.notFound().build() : ResponseEntity.ok(toResponse(ds));
    }

    @Override
    public ResponseEntity<DataSourceResponse> datasourcesIdPut(String id, UpdateDataSourceRequest body) {
        log.debug("Updating data source: {}", id);

        // 1. 先从数据库查询现有数据源
        DataSource existingDs = dataSourceService.get(id);
        if (existingDs == null) {
            log.warn("Data source not found for update: {}", id);
            return ResponseEntity.notFound().build();
        }

        // 2. 只更新传入的非空字段，保持其他字段不变
        if (body.getName() != null && !body.getName().trim().isEmpty()) {
            log.debug("Updating name for datasource {}: {} -> {}", id, existingDs.getName(), body.getName().trim());
            existingDs.setName(body.getName().trim());
        }

        if (body.getDescription() != null) {
            existingDs.setDescription(body.getDescription());
        }

        // 3. 处理config配置 - 只有在传入config时才更新
        if (body.getConfig() != null) {
            if (body.getConfig().isEmpty()) {
                // 如果传入空的config，设置为空JSON对象
                existingDs.setConfig("{}");
            } else {
                try {
                    String configJson = objectMapper.writeValueAsString(body.getConfig());
                    existingDs.setConfig(configJson);
                } catch (Exception e) {
                    log.error("Failed to serialize config to JSON for datasource {}: {}", id, e.getMessage());
                    return ResponseEntity.badRequest().build();
                }
            }
        }
        // 如果没有传入config，保持原有配置不变

        // 4. 更新数据源
        log.debug("Saving updated data source: {}", id);
        DataSource updatedDs = dataSourceService.update(existingDs);
        log.info("Successfully updated data source: {}", id);
        return ResponseEntity.ok(toResponse(updatedDs));
    }

    @Override
    public ResponseEntity<ConnectionTestResult> datasourcesIdTestPost(String id) {
        //TODO
        ConnectionTestResult r = new ConnectionTestResult();
        r.setSuccess(true);
        r.setMessage("OK");
        r.setLatency(10);
        r.setTestedAt(OffsetDateTime.now());
        dataSourceService.updateTestResult(id, true, "OK", 10L);
        return ResponseEntity.ok(r);
    }

    @Override
    public ResponseEntity<DataSourceResponse> datasourcesPost(CreateDataSourceRequest body) {
        log.debug("Creating new data source: {}", body.getName());

        // 1. 验证必填字段
        if (body.getName() == null || body.getName().trim().isEmpty()) {
            log.warn("Data source name is required");
            return ResponseEntity.badRequest().build();
        }

        if (body.getType() == null) {
            log.warn("Data source type is required");
            return ResponseEntity.badRequest().build();
        }

        // 2. 创建数据源对象
        DataSource ds = new DataSource();
        ds.setName(body.getName().trim());
        ds.setDescription(body.getDescription());

        // 3. 处理数据源类型
        try {
            ds.setType(com.dataengine.collection.domain.model.DataSourceType.valueOf(body.getType().getValue()));
        } catch (IllegalArgumentException e) {
            log.error("Invalid data source type: {}", body.getType().getValue());
            return ResponseEntity.badRequest().build();
        }

        // 4. 处理config配置
        if (body.getConfig() != null && !body.getConfig().isEmpty()) {
            try {
                String configJson = objectMapper.writeValueAsString(body.getConfig());
                ds.setConfig(configJson);
            } catch (Exception e) {
                log.error("Failed to serialize config to JSON: {}", e.getMessage());
                return ResponseEntity.badRequest().build();
            }
        } else {
            ds.setConfig("{}");
        }

        // 5. 创建数据源
        try {
            log.debug("Saving new data source: {}", ds.getName());
            DataSource createdDs = dataSourceService.create(ds);
            log.info("Successfully created data source: {} with id: {}", createdDs.getName(), createdDs.getId());
            return ResponseEntity.status(201).body(toResponse(createdDs));
        } catch (Exception e) {
            log.error("Failed to create data source: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().build();
        }
    }
}
