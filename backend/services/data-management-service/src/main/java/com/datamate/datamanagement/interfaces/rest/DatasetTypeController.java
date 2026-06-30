package com.datamate.datamanagement.interfaces.rest;

import com.datamate.datamanagement.interfaces.dto.DatasetTypeResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Arrays;
import java.util.List;

/**
 * 数据集类型 REST 控制器
 */
@RestController
@RequestMapping("/data-management/dataset-types")
public class DatasetTypeController {

    /**
     * 获取所有支持的数据集类型
     * @return 数据集类型列表
     */
    @GetMapping
    public List<DatasetTypeResponse> getDatasetTypes() {
        return Arrays.asList(
            createDatasetType("IMAGE", "图像数据集", "用于机器学习的图像数据集", Arrays.asList("jpg", "jpeg", "png", "bmp", "gif")),
            createDatasetType("TEXT", "文本数据集", "用于文本分析的文本数据集", Arrays.asList("txt", "csv", "json", "xml")),
            createDatasetType("AUDIO", "音频数据集", "用于音频处理的音频数据集", Arrays.asList("wav", "mp3", "flac", "aac")),
            createDatasetType("VIDEO", "视频数据集", "用于视频分析的视频数据集", Arrays.asList("mp4", "avi", "mov", "mkv")),
            createDatasetType("MULTIMODAL", "多模态数据集", "包含多种数据类型的数据集", List.of("*"))
        );
    }

    private DatasetTypeResponse createDatasetType(String code, String name, String description, List<String> supportedFormats) {
        DatasetTypeResponse response = new DatasetTypeResponse();
        response.setCode(code);
        response.setName(name);
        response.setDescription(description);
        response.setSupportedFormats(supportedFormats);
        response.setIcon(getIconForType(code));
        return response;
    }

    private String getIconForType(String typeCode) {
        return switch (typeCode) {
            case "IMAGE" -> "🖼️";
            case "TEXT" -> "📄";
            case "AUDIO" -> "🎵";
            case "VIDEO" -> "🎬";
            case "MULTIMODAL" -> "📊";
            default -> "📁";
        };
    }
}
