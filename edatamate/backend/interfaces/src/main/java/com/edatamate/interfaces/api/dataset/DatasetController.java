package com.edatamate.interfaces.api.dataset;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edatamate.application.dataset.DatasetService;
import com.edatamate.common.dataset.Dataset;
import com.edatamate.common.dataset.dto.DatasetPageQueryDto;
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

    @GetMapping("/{id}")
    public Dataset getDatasetById(@PathVariable Long id) {
        return datasetService.getDatasetById(id);
    }

    @PutMapping("/update")
    public Dataset updateDataset(@RequestBody Dataset dataset) {
        return datasetService.updateDataset(dataset);
    }

    @DeleteMapping("/{id}")
    public void deleteDataset(@PathVariable Long id) {
        datasetService.deleteDataset(id);
    }

    @PostMapping("/page")
    public IPage<Dataset> pageQuery(@RequestBody DatasetPageQueryDto queryDto) {
        return datasetService.pageQuery(queryDto);
    }
}
