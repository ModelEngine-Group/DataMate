package com.edatamate.interfaces.api.dataset;

import com.edatamate.application.dataset.DatasetFileService;
import com.edatamate.common.dataset.DatasetFile;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

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

    /**
     * 批量上传数据集文件
     *
     * @param files 上传的文件列表
     * @param datasetId 数据集ID
     * @return 数据集文件列表
     */
    @PostMapping("/upload/{datasetId}")
    public List<DatasetFile> uploadDatasetFiles(@RequestParam("files") List<MultipartFile> files,
                                                @PathVariable("datasetId") Long datasetId) {
        return datasetFileService.createDatasetFiles(files, datasetId);
    }
}
