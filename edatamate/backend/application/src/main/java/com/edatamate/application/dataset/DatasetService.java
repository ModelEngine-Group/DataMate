package com.edatamate.application.dataset;

import com.alibaba.fastjson2.JSONObject;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edatamate.application.datax.DataXHandler;
import com.edatamate.common.dataset.Dataset;
import com.edatamate.common.dataset.DatasetStatus;
import com.edatamate.common.dataset.FileDownloadRequest;
import com.edatamate.common.dataset.SrcAndDesTypeEnum;
import com.edatamate.common.dataset.dto.DatasetPageQueryDto;
import com.edatamate.domain.repository.DatasetRepository;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.zip.ZipOutputStream;

/**
 * 数据集服务
 *
 * @author: dallas
 * @since: 2025-07-15
 */
@Service
@RequiredArgsConstructor
public class DatasetService {
    private final DatasetRepository datasetRepository;

    private final DatasetFileService datasetFileService;

    private final DataXHandler dataXHandler;

    private final String ZIP_NAME = "dataset_%s.zip";

    @Value("${dataset.file.base-dir:/dataset}")
    private String baseDatasetPath;

    /**
     * 创建数据集
     */
    public Dataset createDataset(Dataset dataset) {
        dataset.setParentId(0L); // 默认父级ID为0
        dataset.setStatus(DatasetStatus.DRAFT);
        String sourceType = dataset.getSrcType();
        String destinationType = dataset.getDesType();
        if ("local".equals(destinationType)) { // 如果目标类型是本地导入, 需要在后台生成一个路径存放数据集
            String destPath = baseDatasetPath + "/" + dataset.getName();
            dataset.setDesConfig(new JSONObject().fluentPut("dest_path", destPath).toString());
        }
        if (SrcAndDesTypeEnum.getRemoteSource().contains(sourceType)) {
            dataXHandler.createJob(dataset.getSrcConfig(), dataset.getDesConfig(), sourceType, destinationType);
        }
        datasetRepository.save(dataset);
        return dataset;
    }

    /**
     * 根据数据集id查询数据集
     */
    public Dataset getDatasetById(Long datasetId) {
        return datasetRepository.getById(datasetId);
    }

    /**
     * 更新数据集
     */
    public Dataset updateDataset(Dataset dataset) {
        datasetRepository.updateById(dataset);
        return dataset;
    }

    /**
     * 删除数据集
     * @param datasetId 数据集ID
     */
    public void deleteDataset(Long datasetId) {
        datasetFileService.deleteDatasetFiles(datasetId);
        datasetRepository.removeById(datasetId);
    }

    /**
     * 分页条件查询数据集
     */
    public IPage<Dataset> pageQuery(DatasetPageQueryDto queryDto) {
        return datasetRepository.pageQuery(queryDto);
    }

    /**
     * 下载数据集或其中部分文件
     */
    public void downloadAsZip(FileDownloadRequest fileDownloadRequest, HttpServletResponse response) {
        response.setContentType("application/zip");
        String zipFileName = String.format(ZIP_NAME, LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss")));
        response.setHeader("Content-Disposition", "attachment; filename=" + zipFileName);
        try (ZipOutputStream zos = new ZipOutputStream(response.getOutputStream())) {
            if (fileDownloadRequest.isFull()) {
                Dataset dataset = datasetRepository.getById(fileDownloadRequest.getDatasetId());
                if (dataset == null) {
                    throw new RuntimeException("数据集不存在");
                }
                fileDownloadRequest.setFileIds(datasetFileService.getFileIdsByDatasetId(fileDownloadRequest.getDatasetId()));
            }
            if (fileDownloadRequest.getFileIds() == null || fileDownloadRequest.getFileIds().isEmpty()) {
                throw new RuntimeException("未指定要下载的文件");
            }
            datasetFileService.zipFiles(fileDownloadRequest.getFileIds(), zos);
        } catch (IOException e) {
            throw new RuntimeException("下载数据集文件失败", e);
        }
    }
}
