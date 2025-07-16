package com.edatamate.interfaces.api.dataset;

import com.edatamate.application.dataset.DatasetFileService;
import com.edatamate.common.dataset.DatasetFile;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 文件管理控制器
 *
 * @author: dallas
 * @since: 2025-07-16
 */
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/dataset/v2/file")
public class DatasetFileController {
    private final DatasetFileService datasetFileService;

    /**
     * 根据ID查询数据集文件
     *
     * @param id 数据集文件ID
     * @return 数据集文件
     */
    @GetMapping("/{id}")
    public DatasetFile getDatasetFileById(@PathVariable Long id) {
        return datasetFileService.getDatasetFileById(id);
    }

    /**
     * 新增数据集文件
     *
     * @param datasetFile 数据集文件
     * @return 数据集文件
     */
    @PostMapping
    public DatasetFile createDatasetFile(@RequestBody DatasetFile datasetFile) {
        return datasetFileService.createDatasetFile(datasetFile);
    }

    /**
     * 更新数据集文件
     *
     * @param datasetFile 数据集文件
     * @return 更新后的数据集文件
     */
    @PutMapping("/{id}")
    public DatasetFile updateDatasetFile(@RequestBody DatasetFile datasetFile) {
        return datasetFileService.updateDatasetFile(datasetFile);
    }

    /**
     * 删除数据集文件
     *
     * @param id 数据集文件ID
     */
    @DeleteMapping("/{id}")
    public void deleteDatasetFile(@PathVariable Long id) {
        datasetFileService.deleteDatasetFile(id);
    }
}

