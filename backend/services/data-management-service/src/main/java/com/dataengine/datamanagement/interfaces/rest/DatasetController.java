package com.dataengine.datamanagement.interfaces.rest;

import com.dataengine.datamanagement.application.service.DatasetApplicationService;
import com.dataengine.datamanagement.domain.model.dataset.Dataset;
import com.dataengine.datamanagement.domain.model.dataset.DatasetStatus;
import com.dataengine.datamanagement.interfaces.api.DatasetApi;
import com.dataengine.datamanagement.interfaces.dto.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RestController;

import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 数据集 REST 控制器
 */
@RestController
public class DatasetController implements DatasetApi {

    private final DatasetApplicationService datasetApplicationService;

    @Autowired
    public DatasetController(DatasetApplicationService datasetApplicationService) {
        this.datasetApplicationService = datasetApplicationService;
    }

    @Override
    public ResponseEntity<PagedDatasetResponse> datasetsGet(Integer page, Integer size, String type, 
                                                          String tags, String keyword, String status) {
        Pageable pageable = PageRequest.of(page != null ? page : 0, size != null ? size : 20);
        
        List<String> tagList = null;
        if (tags != null && !tags.trim().isEmpty()) {
            tagList = Arrays.asList(tags.split(","));
        }
        
        DatasetStatus datasetStatus = null;
        if (status != null) {
            try {
                datasetStatus = DatasetStatus.valueOf(status);
            } catch (IllegalArgumentException e) {
                // 忽略无效状态
            }
        }
        
        Page<Dataset> datasetsPage = datasetApplicationService.getDatasets(type, datasetStatus, keyword, tagList, pageable);
        
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
        
        return ResponseEntity.ok(response);
    }

    @Override
    public ResponseEntity<DatasetResponse> datasetsPost(CreateDatasetRequest createDatasetRequest) {
        try {
            Dataset dataset = datasetApplicationService.createDataset(
                createDatasetRequest.getName(),
                createDatasetRequest.getDescription(),
                createDatasetRequest.getType(),
                getDatasetTypeName(createDatasetRequest.getType()),
                getDatasetTypeDescription(createDatasetRequest.getType()),
                createDatasetRequest.getTags(),
                createDatasetRequest.getDataSource(),
                createDatasetRequest.getTargetLocation(),
                "system" // TODO: 从安全上下文获取当前用户
            );
            
            return ResponseEntity.status(HttpStatus.CREATED).body(convertToResponse(dataset));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().build();
        }
    }

    @Override
    public ResponseEntity<DatasetResponse> datasetsDatasetIdGet(String datasetId) {
        try {
            Dataset dataset = datasetApplicationService.getDataset(datasetId);
            return ResponseEntity.ok(convertToResponse(dataset));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @Override
    public ResponseEntity<DatasetResponse> datasetsDatasetIdPut(String datasetId, UpdateDatasetRequest updateDatasetRequest) {
        try {
            DatasetStatus status = null;
            if (updateDatasetRequest.getStatus() != null) {
                status = DatasetStatus.valueOf(updateDatasetRequest.getStatus().toString());
            }
            
            Dataset dataset = datasetApplicationService.updateDataset(
                datasetId,
                updateDatasetRequest.getName(),
                updateDatasetRequest.getDescription(),
                updateDatasetRequest.getTags(),
                status
            );
            
            return ResponseEntity.ok(convertToResponse(dataset));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @Override
    public ResponseEntity<Void> datasetsDatasetIdDelete(String datasetId) {
        try {
            datasetApplicationService.deleteDataset(datasetId);
            return ResponseEntity.noContent().build();
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @Override
    public ResponseEntity<DatasetStatisticsResponse> datasetsDatasetIdStatisticsGet(String datasetId) {
        try {
            DatasetApplicationService.DatasetStatistics statistics = 
                datasetApplicationService.getDatasetStatistics(datasetId);
            
            DatasetStatisticsResponse response = new DatasetStatisticsResponse();
            response.setTotalFiles(statistics.getTotalFiles());
            response.setCompletedFiles(statistics.getCompletedFiles());
            response.setTotalSize(statistics.getTotalSize());
            response.setCompletionRate(statistics.getCompletionRate());
            response.setFileTypeDistribution(statistics.getFileTypeDistribution());
            response.setStatusDistribution(statistics.getStatusDistribution());
            
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }

    private DatasetResponse convertToResponse(Dataset dataset) {
        DatasetResponse response = new DatasetResponse();
        response.setId(dataset.getId());
        response.setName(dataset.getName());
        response.setDescription(dataset.getDescription());
        
        // 转换数据集类型
        DatasetTypeResponse typeResponse = new DatasetTypeResponse();
        typeResponse.setCode(dataset.getType().getCode());
        typeResponse.setName(dataset.getType().getName());
        typeResponse.setDescription(dataset.getType().getDescription());
        response.setType(typeResponse);
        
        response.setStatus(DatasetResponse.StatusEnum.fromValue(dataset.getStatus().name()));
        response.setDataSource(dataset.getDataSource());
        response.setTargetLocation(dataset.getTargetLocation());
        response.setFileCount(dataset.getFileCount());
        response.setTotalSize(dataset.getTotalSize());
        response.setCompletionRate(dataset.getCompletionRate());
        response.setCreatedAt(dataset.getCreatedAt().atOffset(ZoneOffset.UTC));
        response.setUpdatedAt(dataset.getUpdatedAt().atOffset(ZoneOffset.UTC));
        response.setCreatedBy(dataset.getCreatedBy());
        
        // 转换标签
        List<TagResponse> tagResponses = dataset.getTags().stream()
            .map(tag -> {
                TagResponse tagResponse = new TagResponse();
                tagResponse.setId(tag.getId());
                tagResponse.setName(tag.getName());
                tagResponse.setColor(tag.getColor());
                tagResponse.setDescription(tag.getDescription());
                tagResponse.setUsageCount(tag.getUsageCount());
                return tagResponse;
            })
            .collect(Collectors.toList());
        response.setTags(tagResponses);
        
        return response;
    }

    private String getDatasetTypeName(String typeCode) {
        // 简单的类型映射，实际应用中可以从配置或数据库获取
        switch (typeCode) {
            case "IMAGE": return "图像数据集";
            case "TEXT": return "文本数据集";
            case "AUDIO": return "音频数据集";
            case "VIDEO": return "视频数据集";
            case "MULTIMODAL": return "多模态数据集";
            default: return typeCode;
        }
    }

    private String getDatasetTypeDescription(String typeCode) {
        switch (typeCode) {
            case "IMAGE": return "用于机器学习的图像数据集";
            case "TEXT": return "用于文本分析的文本数据集";
            case "AUDIO": return "用于音频处理的音频数据集";
            case "VIDEO": return "用于视频分析的视频数据集";
            case "MULTIMODAL": return "包含多种数据类型的数据集";
            default: return "数据集类型";
        }
    }
}
