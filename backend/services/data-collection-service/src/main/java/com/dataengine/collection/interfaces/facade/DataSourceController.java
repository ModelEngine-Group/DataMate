package com.dataengine.collection.interfaces.facade;

import com.dataengine.collection.application.service.DataSourceService;
import com.dataengine.collection.domain.model.DataSource;
import com.dataengine.collection.interfaces.api.DataSourceApi;
import com.dataengine.collection.interfaces.dto.*;
import lombok.RequiredArgsConstructor;
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
public class DataSourceController implements DataSourceApi {

    private final DataSourceService dataSourceService;

    private DataSourceResponse toResponse(DataSource ds) {
        DataSourceResponse r = new DataSourceResponse();
        r.setId(ds.getId());
        r.setName(ds.getName());
        r.setDescription(ds.getDescription());
        r.setType(DataSourceType.fromValue(ds.getType().name()));
        r.setStatus(DataSourceResponse.StatusEnum.fromValue(ds.getStatus().name()));
        r.setConfig(Map.of());
        return r;
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
        DataSource ds = dataSourceService.get(id);
        return ds == null ? ResponseEntity.notFound().build() : ResponseEntity.ok(toResponse(ds));
    }

    @Override
    public ResponseEntity<DataSourceResponse> datasourcesIdPut(String id, UpdateDataSourceRequest body) {
        DataSource ds = new DataSource();
        ds.setId(id);
        ds.setName(body.getName());
        ds.setDescription(body.getDescription());
        ds.setType(com.dataengine.collection.domain.model.DataSourceType.MYSQL);
        ds.setConfig("{}");
        ds = dataSourceService.update(ds);
        return ResponseEntity.ok(toResponse(ds));
    }

    @Override
    public ResponseEntity<ConnectionTestResult> datasourcesIdTestPost(String id) {
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
        DataSource ds = new DataSource();
        ds.setName(body.getName());
        ds.setDescription(body.getDescription());
        ds.setType(com.dataengine.collection.domain.model.DataSourceType.valueOf(body.getType().getValue()));
        ds.setConfig("{}");
        ds = dataSourceService.create(ds);
        return ResponseEntity.status(201).body(toResponse(ds));
    }
}
