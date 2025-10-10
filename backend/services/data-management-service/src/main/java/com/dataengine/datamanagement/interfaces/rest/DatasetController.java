package com.dataengine.datamanagement.interfaces.rest;

import com.dataengine.datamanagement.application.service.DatasetApplicationService;
import com.dataengine.datamanagement.domain.model.dataset.Dataset;
import com.dataengine.datamanagement.interfaces.dto.*;
import com.dataengine.common.interfaces.Response;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.ZoneOffset;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 数据集 REST 控制器（UUID 模式）
 */
@RestController
@RequestMapping("/data-management/datasets")
public class DatasetController {

    private final DatasetApplicationService datasetApplicationService;

    @Autowired
    public DatasetController(DatasetApplicationService datasetApplicationService) {
        this.datasetApplicationService = datasetApplicationService;
    }

    @GetMapping
    public ResponseEntity<Response<PagedDatasetResponse>> getDatasets(
            @RequestParam(value = "page", required = false, defaultValue = "0") Integer page,
            @RequestParam(value = "size", required = false, defaultValue = "20") Integer size,
            @RequestParam(value = "type", required = false) String type,
            @RequestParam(value = "tags", required = false) String tags,
            @RequestParam(value = "keyword", required = false) String keyword,
            @RequestParam(value = "status", required = false) String status) {

        Pageable pageable = PageRequest.of(page != null ? page : 0, size != null ? size : 20);

        List<String> tagList = null;
        if (tags != null && !tags.trim().isEmpty()) {
            tagList = Arrays.asList(tags.split(","));
        }

        Page<Dataset> datasetsPage = datasetApplicationService.getDatasets(type, status, keyword, tagList, pageable);

        PagedDatasetResponse response = new PagedDatasetResponse();
        response.setContent(datasetsPage.getContent().stream()
                .map(this::convertToResponse)
                .collect(Collectors.toList()));
        response.setPage(datasetsPage.getNumber());
        response.setSize(datasetsPage.getSize());
        response.setTotalElements((int) datasetsPage.getTotalElements());
        response.setTotalPages(datasetsPage.getTotalPages());
        response.setFirst(datasetsPage.isFirst());
        response.setLast(datasetsPage.isLast());

        return ResponseEntity.ok(Response.ok(response));
    }

    @PostMapping
    public ResponseEntity<Response<DatasetResponse>> createDataset(@RequestBody CreateDatasetRequest createDatasetRequest) {
        try {
            Long dataSourceId = null;
            if (createDatasetRequest.getDataSource() != null) {
                try { dataSourceId = Long.valueOf(createDatasetRequest.getDataSource()); } catch (NumberFormatException ignore) {}
            }
            Dataset dataset = datasetApplicationService.createDataset(
                    createDatasetRequest.getName(),
                    createDatasetRequest.getDescription(),
                    createDatasetRequest.getType(),
                    createDatasetRequest.getTags(),
                    dataSourceId,
                    createDatasetRequest.getTargetLocation(),
                    null,
                    "system"
            );
            return ResponseEntity.status(HttpStatus.CREATED).body(Response.ok(convertToResponse(dataset)));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Response.error("参数错误", null));
        }
    }

    @GetMapping("/{datasetId}")
    public ResponseEntity<Response<DatasetResponse>> getDatasetById(@PathVariable("datasetId") String datasetId) {
        try {
            Dataset dataset = datasetApplicationService.getDataset(datasetId);
            return ResponseEntity.ok(Response.ok(convertToResponse(dataset)));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Response.error("数据集不存在", null));
        }
    }

    @PutMapping("/{datasetId}")
    public ResponseEntity<Response<DatasetResponse>> updateDataset(
            @PathVariable("datasetId") String datasetId,
            @RequestBody UpdateDatasetRequest updateDatasetRequest) {
        try {
            Dataset dataset = datasetApplicationService.updateDataset(
                    datasetId,
                    updateDatasetRequest.getName(),
                    updateDatasetRequest.getDescription(),
                    updateDatasetRequest.getTags(),
                    updateDatasetRequest.getStatus() != null ? updateDatasetRequest.getStatus() : null
            );
            return ResponseEntity.ok(Response.ok(convertToResponse(dataset)));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Response.error("数据集不存在", null));
        }
    }

    @DeleteMapping("/{datasetId}")
    public ResponseEntity<Response<Void>> deleteDataset(@PathVariable("datasetId") String datasetId) {
        try {
            datasetApplicationService.deleteDataset(datasetId);
            return ResponseEntity.noContent().build();
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Response.error("数据集不存在", null));
        }
    }

    @GetMapping("/{datasetId}/statistics")
    public ResponseEntity<Response<DatasetStatisticsResponse>> getDatasetStatistics(@PathVariable("datasetId") String datasetId) {
        try {
            Map<String, Object> stats = datasetApplicationService.getDatasetStatistics(datasetId);

            DatasetStatisticsResponse response = new DatasetStatisticsResponse();
            response.setTotalFiles((Integer) stats.get("totalFiles"));
            response.setCompletedFiles((Integer) stats.get("completedFiles"));
            response.setTotalSize((Long) stats.get("totalSize"));
            response.setCompletionRate((Float) stats.get("completionRate"));
            response.setFileTypeDistribution((Map<String, Integer>) stats.get("fileTypeDistribution"));
            response.setStatusDistribution((Map<String, Integer>) stats.get("statusDistribution"));

            return ResponseEntity.ok(Response.ok(response));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Response.error("数据集不存在", null));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Response.error("服务器内部错误", null));
        }
    }

    @GetMapping("/statistics")
    public ResponseEntity<Response<AllDatasetStatisticsResponse>> getAllStatistics() {
        return ResponseEntity.ok(Response.ok(datasetApplicationService.getAllDatasetStatistics()));
    }

    private DatasetResponse convertToResponse(Dataset dataset) {
        DatasetResponse response = new DatasetResponse();
        response.setId(dataset.getId());
        response.setName(dataset.getName());
        response.setDescription(dataset.getDescription());

        DatasetTypeResponse typeResponse = new DatasetTypeResponse();
        typeResponse.setCode(dataset.getDatasetType());
        response.setType(typeResponse);

        response.setStatus(dataset.getStatus());

        response.setDataSource(dataset.getDataSourceId() != null ? String.valueOf(dataset.getDataSourceId()) : null);
        response.setTargetLocation(dataset.getPath());
        response.setFileCount(dataset.getFileCount() != null ? dataset.getFileCount().intValue() : null);
        response.setTotalSize(dataset.getSizeBytes());
        response.setCompletionRate(dataset.getCompletionRate() != null ? dataset.getCompletionRate().floatValue() : null);

        if (dataset.getCreatedAt() != null) response.setCreatedAt(dataset.getCreatedAt().atOffset(ZoneOffset.UTC).toLocalDateTime());
        if (dataset.getUpdatedAt() != null) response.setUpdatedAt(dataset.getUpdatedAt().atOffset(ZoneOffset.UTC).toLocalDateTime());
        response.setCreatedBy(dataset.getCreatedBy());

        List<TagResponse> tagResponses = dataset.getTags().stream()
                .map(tag -> {
                    TagResponse tr = new TagResponse();
                    tr.setId(tag.getId());
                    tr.setName(tag.getName());
                    tr.setColor(tag.getColor());
                    tr.setDescription(tag.getDescription());
                    tr.setUsageCount(tag.getUsageCount() != null ? tag.getUsageCount().intValue() : null);
                    return tr;
                })
                .collect(Collectors.toList());
        response.setTags(tagResponses);

        return response;
    }
}
