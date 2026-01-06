package com.datamate.datamanagement.application;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.datamate.common.domain.utils.ChunksSaver;
import com.datamate.common.setting.application.SysParamApplicationService;
import com.datamate.datamanagement.interfaces.dto.*;
import com.datamate.common.infrastructure.exception.BusinessAssert;
import com.datamate.common.interfaces.PagedResponse;
import com.datamate.datamanagement.domain.model.dataset.Dataset;
import com.datamate.datamanagement.domain.model.dataset.DatasetFile;
import com.datamate.datamanagement.domain.model.dataset.Tag;
import com.datamate.datamanagement.infrastructure.client.CollectionTaskClient;
import com.datamate.datamanagement.infrastructure.client.dto.CollectionTaskDetailResponse;
import com.datamate.datamanagement.infrastructure.exception.DataManagementErrorCode;
import com.datamate.datamanagement.infrastructure.persistence.mapper.TagMapper;
import com.datamate.datamanagement.infrastructure.persistence.repository.DatasetFileRepository;
import com.datamate.datamanagement.infrastructure.persistence.repository.DatasetRepository;
import com.datamate.datamanagement.interfaces.converter.DatasetConverter;
import com.datamate.datamanagement.interfaces.dto.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * 数据集应用服务（对齐 DB schema，使用 UUID 字符串主键）
 */
@Slf4j
@Service
@Transactional
@RequiredArgsConstructor
public class DatasetApplicationService {
    private static final String DATASET_PVC_NAME = "sys.management.dataset.pvc.name";
    private final DatasetRepository datasetRepository;
    private final TagMapper tagMapper;
    private final DatasetFileRepository datasetFileRepository;
    private final CollectionTaskClient collectionTaskClient;
    private final DatasetFileApplicationService datasetFileApplicationService;
    private final SysParamApplicationService sysParamService;

    @Value("${datamate.data-management.base-path:/dataset}")
    private String datasetBasePath;

    /**
     * 创建数据集
     */
    @Transactional
    public Dataset createDataset(CreateDatasetRequest createDatasetRequest) {
        BusinessAssert.isTrue(datasetRepository.findByName(createDatasetRequest.getName()) == null, DataManagementErrorCode.DATASET_ALREADY_EXISTS);
        // 创建数据集对象
        Dataset dataset = DatasetConverter.INSTANCE.convertToDataset(createDatasetRequest);
        dataset.initCreateParam(datasetBasePath);
        // 处理标签
        Set<Tag> processedTags = Optional.ofNullable(createDatasetRequest.getTags())
            .filter(CollectionUtils::isNotEmpty)
            .map(this::processTagNames)
            .orElseGet(HashSet::new);
        dataset.setTags(processedTags);
        datasetRepository.save(dataset);

        //todo 需要解耦这块逻辑
        if (StringUtils.hasText(createDatasetRequest.getDataSource())) {
            // 数据源id不为空，使用异步线程进行文件扫盘落库
            processDataSourceAsync(dataset.getId(), createDatasetRequest.getDataSource());
        }
        return dataset;
    }

    public String getDatasetPvcName() {
        return sysParamService.getParamByKey(DATASET_PVC_NAME);
    }

    public Dataset updateDataset(String datasetId, UpdateDatasetRequest updateDatasetRequest) {
        Dataset dataset = datasetRepository.getById(datasetId);
        BusinessAssert.notNull(dataset, DataManagementErrorCode.DATASET_NOT_FOUND);
        if (StringUtils.hasText(updateDatasetRequest.getName())) {
            dataset.setName(updateDatasetRequest.getName());
        }
        if (StringUtils.hasText(updateDatasetRequest.getDescription())) {
            dataset.setDescription(updateDatasetRequest.getDescription());
        }
        if (CollectionUtils.isNotEmpty(updateDatasetRequest.getTags())) {
            dataset.setTags(processTagNames(updateDatasetRequest.getTags()));
        }
        if (Objects.nonNull(updateDatasetRequest.getStatus())) {
            dataset.setStatus(updateDatasetRequest.getStatus());
        }
        if (StringUtils.hasText(updateDatasetRequest.getDataSource())) {
            // 数据源id不为空，使用异步线程进行文件扫盘落库
            processDataSourceAsync(dataset.getId(), updateDatasetRequest.getDataSource());
        }
        datasetRepository.updateById(dataset);
        return dataset;
    }

    /**
     * 删除数据集
     */
    @Transactional
    public void deleteDataset(String datasetId) {
        Dataset dataset = datasetRepository.getById(datasetId);
        datasetRepository.removeById(datasetId);
        if (dataset != null) {
            ChunksSaver.deleteFolder(dataset.getPath());
        }
    }

    /**
     * 获取数据集详情
     */
    @Transactional(readOnly = true)
    public Dataset getDataset(String datasetId) {
        Dataset dataset = datasetRepository.getById(datasetId);
        BusinessAssert.notNull(dataset, DataManagementErrorCode.DATASET_NOT_FOUND);
        List<DatasetFile> datasetFiles = datasetFileRepository.findAllByDatasetId(datasetId);
        dataset.setFiles(datasetFiles);
        return dataset;
    }

    /**
     * 分页查询数据集
     */
    @Transactional(readOnly = true)
    public PagedResponse<DatasetResponse> getDatasets(DatasetPagingQuery query) {
        IPage<Dataset> page = new Page<>(query.getPage(), query.getSize());
        page = datasetRepository.findByCriteria(page, query);
        String datasetPvcName = getDatasetPvcName();
        List<DatasetResponse> datasetResponses = DatasetConverter.INSTANCE.convertToResponse(page.getRecords());
        datasetResponses.forEach(dataset -> dataset.setPvcName(datasetPvcName));
        return PagedResponse.of(datasetResponses, page.getCurrent(), page.getTotal(), page.getPages());
    }

    /**
     * 处理标签名称，创建或获取标签
     */
    private Set<Tag> processTagNames(List<String> tagNames) {
        Set<Tag> tags = new HashSet<>();
        for (String tagName : tagNames) {
            Tag tag = tagMapper.findByName(tagName);
            if (tag == null) {
                Tag newTag = new Tag(tagName, null, null, "#007bff");
                newTag.setUsageCount(0L);
                newTag.setId(UUID.randomUUID().toString());
                tagMapper.insert(newTag);
                tag = newTag;
            }
            tag.setUsageCount(tag.getUsageCount() == null ? 1L : tag.getUsageCount() + 1);
            tagMapper.updateUsageCount(tag.getId(), tag.getUsageCount());
            tags.add(tag);
        }
        return tags;
    }

    /**
     * 获取数据集统计信息
     */
    @Transactional(readOnly = true)
    public Map<String, Object> getDatasetStatistics(String datasetId) {
        Dataset dataset = datasetRepository.getById(datasetId);
        if (dataset == null) {
            throw new IllegalArgumentException("Dataset not found: " + datasetId);
        }

        Map<String, Object> statistics = new HashMap<>();

        // 基础统计
        Long totalFiles = datasetFileRepository.countByDatasetId(datasetId);
        Long completedFiles = datasetFileRepository.countCompletedByDatasetId(datasetId);
        Long totalSize = datasetFileRepository.sumSizeByDatasetId(datasetId);

        statistics.put("totalFiles", totalFiles != null ? totalFiles.intValue() : 0);
        statistics.put("completedFiles", completedFiles != null ? completedFiles.intValue() : 0);
        statistics.put("totalSize", totalSize != null ? totalSize : 0L);

        // 完成率计算
        float completionRate = 0.0f;
        if (totalFiles != null && totalFiles > 0) {
            completionRate = (completedFiles != null ? completedFiles.floatValue() : 0.0f) / totalFiles.floatValue() * 100.0f;
        }
        statistics.put("completionRate", completionRate);

        // 文件类型分布统计
        Map<String, Integer> fileTypeDistribution = new HashMap<>();
        List<DatasetFile> allFiles = datasetFileRepository.findAllByDatasetId(datasetId);
        if (allFiles != null) {
            for (DatasetFile file : allFiles) {
                String fileType = file.getFileType() != null ? file.getFileType() : "unknown";
                fileTypeDistribution.put(fileType, fileTypeDistribution.getOrDefault(fileType, 0) + 1);
            }
        }
        statistics.put("fileTypeDistribution", fileTypeDistribution);

        // 状态分布统计
        Map<String, Integer> statusDistribution = new HashMap<>();
        if (allFiles != null) {
            for (DatasetFile file : allFiles) {
                String status = file.getStatus() != null ? file.getStatus() : "unknown";
                statusDistribution.put(status, statusDistribution.getOrDefault(status, 0) + 1);
            }
        }
        statistics.put("statusDistribution", statusDistribution);

        return statistics;
    }

    /**
     * 获取所有数据集的汇总统计信息
     */
    public AllDatasetStatisticsResponse getAllDatasetStatistics() {
        return datasetRepository.getAllDatasetStatistics();
    }

    /**
     * 异步处理数据源文件扫描
     *
     * @param datasetId    数据集ID
     * @param dataSourceId 数据源ID（归集任务ID）
     */
    @Async
    public void processDataSourceAsync(String datasetId, String dataSourceId) {
        try {
            log.info("Initiating data source file scanning, dataset ID: {}, collection task ID: {}", datasetId, dataSourceId);
            List<String> filePaths = getFilePaths(dataSourceId);
            if (CollectionUtils.isEmpty(filePaths)) {
                return;
            }
            datasetFileApplicationService.copyFilesToDatasetDir(datasetId, new CopyFilesRequest(filePaths));
            log.info("Success file scan, total files: {}", filePaths.size());
        } catch (Exception e) {
            log.error("处理数据源文件扫描失败，数据集ID: {}, 数据源ID: {}", datasetId, dataSourceId, e);
        }
    }

    private List<String> getFilePaths(String dataSourceId) {
        CollectionTaskDetailResponse taskDetail = collectionTaskClient.getTaskDetail(dataSourceId).getData();
        if (taskDetail == null) {
            log.warn("Fail to get collection task detail, task ID: {}", dataSourceId);
            return Collections.emptyList();
        }
        Path targetPath = Paths.get(taskDetail.getTargetPath());
        if (!Files.exists(targetPath) || !Files.isDirectory(targetPath)) {
            log.warn("Target path not exists or is not a directory: {}", taskDetail.getTargetPath());
            return Collections.emptyList();
        }

        try (Stream<Path> paths = Files.walk(targetPath, 1)) {
            return paths
                .filter(Files::isRegularFile)  // 只保留文件，排除目录
                .map(Path::toString)           // 转换为字符串路径
                .collect(Collectors.toList());
        } catch (IOException e) {
            log.error("Fail to scan directory: {}", targetPath, e);
            return Collections.emptyList();
        }
    }
}
