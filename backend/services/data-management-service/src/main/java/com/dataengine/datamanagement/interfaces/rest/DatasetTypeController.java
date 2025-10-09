package com.dataengine.datamanagement.interfaces.rest;

import com.dataengine.datamanagement.interfaces.api.DatasetTypeApi;
import com.dataengine.datamanagement.interfaces.dto.DatasetTypeResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RestController;

import java.util.Arrays;
import java.util.List;

/**
 * 数据集类型 REST 控制器
 */
@RestController
public class DatasetTypeController implements DatasetTypeApi {

    @Override
    public ResponseEntity<List<DatasetTypeResponse>> getDatasetTypes() {
        // 硬编码的数据集类型，实际应用中可以从数据库获取
        List<DatasetTypeResponse> types = Arrays.asList(
            createDatasetType("IMAGE", "图像数据集", "用于机器学习的图像数据集", Arrays.asList("jpg", "jpeg", "png", "bmp", "gif")),
            createDatasetType("TEXT", "文本数据集", "用于文本分析的文本数据集", Arrays.asList("txt", "csv", "json", "xml")),
            createDatasetType("AUDIO", "音频数据集", "用于音频处理的音频数据集", Arrays.asList("wav", "mp3", "flac", "aac")),
            createDatasetType("VIDEO", "视频数据集", "用于视频分析的视频数据集", Arrays.asList("mp4", "avi", "mov", "mkv")),
            createDatasetType("MULTIMODAL", "多模态数据集", "包含多种数据类型的数据集", Arrays.asList("*"))
        );

        return ResponseEntity.ok(types);
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
        switch (typeCode) {
            case "IMAGE": return "🖼️";
            case "TEXT": return "📄";
            case "AUDIO": return "🎵";
            case "VIDEO": return "🎬";
            case "MULTIMODAL": return "📊";
            default: return "📁";
        }
    }
}
