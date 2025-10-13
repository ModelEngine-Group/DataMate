package com.dataengine.datamanagement.interfaces.rest;

import com.dataengine.common.interfaces.PagedResponse;
import com.dataengine.datamanagement.application.service.DatasetApplicationService;
import com.dataengine.datamanagement.domain.model.dataset.Dataset;
import com.dataengine.datamanagement.interfaces.converter.DatasetConverter;
import com.dataengine.datamanagement.interfaces.dto.*;
import com.dataengine.common.interfaces.Response;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

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

    /**
     * 获取数据集列表
     *
     * @param query 分页查询参数
     * @return 分页的数据集列表
     */
    @GetMapping
    public ResponseEntity<Response<PagedResponse<DatasetResponse>>> getDatasets(DatasetPagingQuery query) {
        query.initPaging();
        Page<Dataset> datasetsPage = datasetApplicationService.getDatasets(query);
        return ResponseEntity.ok(Response.ok(DatasetConverter.INSTANCE.convertToPagedResponse(datasetsPage)));
    }

    @PostMapping
    public ResponseEntity<Response<DatasetResponse>> createDataset(@RequestBody CreateDatasetRequest createDatasetRequest) {
        try {
            Dataset dataset = datasetApplicationService.createDataset(createDatasetRequest);
            return ResponseEntity.status(HttpStatus.CREATED).body(Response.ok(DatasetConverter.INSTANCE.convertToResponse(dataset)));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Response.error("参数错误", null));
        }
    }

    @GetMapping("/{datasetId}")
    public ResponseEntity<Response<DatasetResponse>> getDatasetById(@PathVariable("datasetId") String datasetId) {
        try {
            Dataset dataset = datasetApplicationService.getDataset(datasetId);
            return ResponseEntity.ok(Response.ok(DatasetConverter.INSTANCE.convertToResponse(dataset)));
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
            return ResponseEntity.ok(Response.ok(DatasetConverter.INSTANCE.convertToResponse(dataset)));
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
}
