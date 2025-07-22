package com.edatamate.application.dataset;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edatamate.common.dataset.Dataset;
import com.edatamate.common.dataset.FileDownloadRequest;
import com.edatamate.common.dataset.dto.DatasetPageQueryDto;
import com.edatamate.domain.dataset.service.DatasetDomainService;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
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

    private final DatasetFileService datasetFileService;

    private final DatasetDomainService datasetDomainService;

    /**
     * 创建数据集
     */
    public Dataset createDataset(Dataset dataset) {
        // 待添加业务校验逻辑
        return datasetDomainService.createDataset(dataset);
    }

    /**
     * 根据数据集id查询数据集
     */
    public Dataset getDatasetById(Long datasetId) {
        return datasetDomainService.getDatasetById(datasetId);
    }

    /**
     * 更新数据集
     */
    public Dataset updateDataset(Dataset dataset) {
        // 待添加业务校验逻辑
        return datasetDomainService.updateDataset(dataset);
    }

    /**
     * 删除数据集
     * @param datasetId 数据集ID
     */
    public void deleteDataset(Long datasetId) {
        // 待添加业务校验逻辑
        datasetFileService.deleteDatasetFiles(datasetId);
        datasetDomainService.deleteDataset(datasetId);
    }

    /**
     * 分页条件查询数据集
     */
    public IPage<Dataset> pageQuery(DatasetPageQueryDto queryDto) {
        return datasetDomainService.pageQuery(queryDto);
    }

    /**
     * 下载数据集或其中部分文件
     */
    public void downloadAsZip(FileDownloadRequest fileDownloadRequest, HttpServletResponse response) {
        response.setContentType("application/zip");
        String ZIP_NAME = "dataset_%s.zip";
        String zipFileName = String.format(ZIP_NAME, LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss")));
        response.setHeader("Content-Disposition", "attachment; filename=" + zipFileName);
        try (ZipOutputStream zos = new ZipOutputStream(response.getOutputStream())) {
            if (fileDownloadRequest.isFull()) {
                Dataset dataset = datasetDomainService.getDatasetById(fileDownloadRequest.getDatasetId());
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
