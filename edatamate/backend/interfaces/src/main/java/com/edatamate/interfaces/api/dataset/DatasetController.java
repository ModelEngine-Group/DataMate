package com.edatamate.interfaces.api.dataset;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edatamate.application.dataset.DatasetService;
import com.edatamate.common.dataset.Dataset;
import com.edatamate.common.dataset.FileDownloadRequest;
import com.edatamate.common.dataset.dto.DatasetPageQueryDto;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 数据集控制器
 *
 * @author: dallas
 * @since: 2025-07-11
 */
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/dataset/v2")
public class DatasetController {
    private final DatasetService datasetService;

    @PostMapping("/create")
    public Dataset createDataset(@RequestBody Dataset dataset) {
        return datasetService.createDataset(dataset);
    }

    @GetMapping("/{dataset_id}")
    public Dataset getDatasetById(@PathVariable("dataset_id") Long datasetId) {
        return datasetService.getDatasetById(datasetId);
    }

    @PutMapping("/update")
    public Dataset updateDataset(@RequestBody Dataset dataset) {
        return datasetService.updateDataset(dataset);
    }

    /**
     * 删除数据集
     *
     * @param datasetId 数据集ID
     */
    @DeleteMapping("/{dataset_id}")
    public void deleteDataset(@PathVariable("dataset_id") Long datasetId) {
        datasetService.deleteDataset(datasetId);
    }

    /**
     * 查询数据集信息
     *
     * @param queryDto 数据集查询条件
     */
    @PostMapping("/page")
    public IPage<Dataset> pageQuery(@RequestBody DatasetPageQueryDto queryDto) {
        return datasetService.pageQuery(queryDto);
    }

    /**
     * 下载数据集或其中部分文件
     *
     * @param downloadReq 下载亲求
     */
    @GetMapping("/download")
    public void downloadDataset(@RequestBody FileDownloadRequest downloadReq, HttpServletResponse response) {
        datasetService.downloadAsZip(downloadReq, response);
    }
}
