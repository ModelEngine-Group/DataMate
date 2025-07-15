package com.edatamate.interfaces.api.dataset;

import com.edatamate.application.dataset.DatasetService;
import com.edatamate.common.dataset.Dataset;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

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

    @GetMapping("/list")
    public List<Dataset> getDatasets() {
        return datasetService.getDatasets();
    }
}
