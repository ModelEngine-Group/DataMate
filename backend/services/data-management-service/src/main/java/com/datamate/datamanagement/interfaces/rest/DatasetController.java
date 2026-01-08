package com.datamate.datamanagement.interfaces.rest;

import com.datamate.datamanagement.interfaces.dto.*;
import com.datamate.common.infrastructure.common.Response;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.datamate.common.interfaces.PagedResponse;
import com.datamate.datamanagement.application.DatasetApplicationService;
import com.datamate.datamanagement.domain.model.dataset.Dataset;
import com.datamate.datamanagement.interfaces.converter.DatasetConverter;
import com.datamate.datamanagement.interfaces.dto.*;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springaicommunity.mcp.annotation.McpTool;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 数据集 REST 控制器
 */
@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/data-management/datasets")
public class DatasetController {
    private final DatasetApplicationService datasetApplicationService;

    /**
     * 获取数据集列表
     *
     * @param query 分页查询参数
     * @return 分页的数据集列表
     */
    @GetMapping
    @McpTool(name = "query_datasets", description = "根据参数查询满足条件的数据集列表")
    public PagedResponse<DatasetResponse> getDatasets(DatasetPagingQuery query) {
        return datasetApplicationService.getDatasets(query);
    }

    /**
     * 创建数据集
     *
     * @param createDatasetRequest 创建数据集请求参数
     * @return 创建的数据集响应
     */
    @PostMapping
    @McpTool(name = "create_dataset", description = "创建数据集")
    public DatasetResponse createDataset(@RequestBody @Valid CreateDatasetRequest createDatasetRequest) {
        Dataset dataset = datasetApplicationService.createDataset(createDatasetRequest);
        return DatasetConverter.INSTANCE.convertToResponse(dataset);
    }

    /**
     * 根据ID获取数据集详情
     *
     * @param datasetId 数据集ID
     * @return 数据集响应
     */
    @GetMapping("/{datasetId}")
    public DatasetResponse getDatasetById(@PathVariable("datasetId") String datasetId) {
        DatasetResponse dataset = DatasetConverter.INSTANCE.convertToResponse(datasetApplicationService.getDataset(datasetId));
        dataset.setPvcName(datasetApplicationService.getDatasetPvcName());
        return dataset;
    }

    /**
     * 根据ID更新数据集
     *
     * @param datasetId            数据集ID
     * @param updateDatasetRequest 更新数据集请求参数
     * @return 更新后的数据集响应
     */
    @PutMapping("/{datasetId}")
    public DatasetResponse updateDataset(@PathVariable("datasetId") String datasetId,
                                         @RequestBody UpdateDatasetRequest updateDatasetRequest) {
        Dataset dataset = datasetApplicationService.updateDataset(datasetId, updateDatasetRequest);
        return DatasetConverter.INSTANCE.convertToResponse(dataset);
    }

    /**
     * 根据ID删除数据集
     *
     * @param datasetId 数据集ID
     */
    @DeleteMapping("/{datasetId}")
    public void deleteDataset(@PathVariable("datasetId") String datasetId) {
        datasetApplicationService.deleteDataset(datasetId);
    }

    @GetMapping("/{datasetId}/statistics")
    public ResponseEntity<Response<DatasetStatisticsResponse>> getDatasetStatistics(
        @PathVariable("datasetId") String datasetId) {
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
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Response.error(SystemErrorCode.UNKNOWN_ERROR, null));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Response.error(SystemErrorCode.UNKNOWN_ERROR, null));
        }
    }

    @GetMapping("/statistics")
    public ResponseEntity<Response<AllDatasetStatisticsResponse>> getAllStatistics() {
        return ResponseEntity.ok(Response.ok(datasetApplicationService.getAllDatasetStatistics()));
    }
}
