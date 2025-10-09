package com.dataengine.datamanagement.interfaces.rest;

import com.dataengine.datamanagement.interfaces.dto.DatasetTypeResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
class DatasetTypeControllerTest {

    @InjectMocks
    private DatasetTypeController controller;

    @BeforeEach
    void setUp() {
        controller = new DatasetTypeController();
    }

    @Test
    @DisplayName("datasetTypesGet: 返回所有数据集类型")
    void getDatasetTypes_success() {
        ResponseEntity<List<DatasetTypeResponse>> response = controller.getDatasetTypes();

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(5, response.getBody().size());

        List<DatasetTypeResponse> types = response.getBody();

        // 验证IMAGE类型
        DatasetTypeResponse imageType = types.stream()
                .filter(type -> "IMAGE".equals(type.getCode()))
                .findFirst()
                .orElse(null);
        assertNotNull(imageType);
        assertEquals("IMAGE", imageType.getCode());
        assertEquals("图像数据集", imageType.getName());
        assertEquals("用于机器学习的图像数据集", imageType.getDescription());
        assertEquals("🖼️", imageType.getIcon());
        assertTrue(imageType.getSupportedFormats().contains("jpg"));
        assertTrue(imageType.getSupportedFormats().contains("png"));

        // 验证TEXT类型
        DatasetTypeResponse textType = types.stream()
                .filter(type -> "TEXT".equals(type.getCode()))
                .findFirst()
                .orElse(null);
        assertNotNull(textType);
        assertEquals("TEXT", textType.getCode());
        assertEquals("文本数据集", textType.getName());
        assertEquals("用于文本分析的文本数据集", textType.getDescription());
        assertEquals("📄", textType.getIcon());
        assertTrue(textType.getSupportedFormats().contains("txt"));
        assertTrue(textType.getSupportedFormats().contains("csv"));
        assertTrue(textType.getSupportedFormats().contains("json"));

        // 验证AUDIO类型
        DatasetTypeResponse audioType = types.stream()
                .filter(type -> "AUDIO".equals(type.getCode()))
                .findFirst()
                .orElse(null);
        assertNotNull(audioType);
        assertEquals("AUDIO", audioType.getCode());
        assertEquals("音频数据集", audioType.getName());
        assertEquals("用于音频处理的音频数据集", audioType.getDescription());
        assertEquals("🎵", audioType.getIcon());
        assertTrue(audioType.getSupportedFormats().contains("wav"));
        assertTrue(audioType.getSupportedFormats().contains("mp3"));

        // 验证VIDEO类型
        DatasetTypeResponse videoType = types.stream()
                .filter(type -> "VIDEO".equals(type.getCode()))
                .findFirst()
                .orElse(null);
        assertNotNull(videoType);
        assertEquals("VIDEO", videoType.getCode());
        assertEquals("视频数据集", videoType.getName());
        assertEquals("用于视频分析的视频数据集", videoType.getDescription());
        assertEquals("🎬", videoType.getIcon());
        assertTrue(videoType.getSupportedFormats().contains("mp4"));
        assertTrue(videoType.getSupportedFormats().contains("avi"));

        // 验证MULTIMODAL类型
        DatasetTypeResponse multimodalType = types.stream()
                .filter(type -> "MULTIMODAL".equals(type.getCode()))
                .findFirst()
                .orElse(null);
        assertNotNull(multimodalType);
        assertEquals("MULTIMODAL", multimodalType.getCode());
        assertEquals("多模态数据集", multimodalType.getName());
        assertEquals("包含多种数据类型的数据集", multimodalType.getDescription());
        assertEquals("📊", multimodalType.getIcon());
        assertTrue(multimodalType.getSupportedFormats().contains("*"));
    }

    @Test
    @DisplayName("datasetTypesGet: 验证返回的数据集类型顺序")
    void getDatasetTypes_orderVerification() {
        ResponseEntity<List<DatasetTypeResponse>> response = controller.getDatasetTypes();

        List<DatasetTypeResponse> types = response.getBody();
        assertNotNull(types);

        // 验证返回顺序
        assertEquals("IMAGE", types.get(0).getCode());
        assertEquals("TEXT", types.get(1).getCode());
        assertEquals("AUDIO", types.get(2).getCode());
        assertEquals("VIDEO", types.get(3).getCode());
        assertEquals("MULTIMODAL", types.get(4).getCode());
    }

    @Test
    @DisplayName("datasetTypesGet: 验证每个类型都有必要属性")
    void getDatasetTypes_requiredProperties() {
        ResponseEntity<List<DatasetTypeResponse>> response = controller.getDatasetTypes();

        List<DatasetTypeResponse> types = response.getBody();
        assertNotNull(types);

        for (DatasetTypeResponse type : types) {
            assertNotNull(type.getCode(), "Code should not be null");
            assertNotNull(type.getName(), "Name should not be null");
            assertNotNull(type.getDescription(), "Description should not be null");
            assertNotNull(type.getSupportedFormats(), "SupportedFormats should not be null");
            assertFalse(type.getSupportedFormats().isEmpty(), "SupportedFormats should not be empty");
            assertNotNull(type.getIcon(), "Icon should not be null");
            assertFalse(type.getCode().isEmpty(), "Code should not be empty");
            assertFalse(type.getName().isEmpty(), "Name should not be empty");
            assertFalse(type.getDescription().isEmpty(), "Description should not be empty");
        }
    }

    @Test
    @DisplayName("datasetTypesGet: 验证支持的格式不为空")
    void getDatasetTypes_supportedFormatsNotEmpty() {
        ResponseEntity<List<DatasetTypeResponse>> response = controller.getDatasetTypes();

        List<DatasetTypeResponse> types = response.getBody();
        assertNotNull(types);

        for (DatasetTypeResponse type : types) {
            assertNotNull(type.getSupportedFormats());
            assertFalse(type.getSupportedFormats().isEmpty());

            // 确保每个支持的格式都不为空字符串
            for (String format : type.getSupportedFormats()) {
                assertNotNull(format);
                assertFalse(format.trim().isEmpty());
            }
        }
    }

    @Test
    @DisplayName("datasetTypesGet: 验证图标映射")
    void getDatasetTypes_iconMapping() {
        ResponseEntity<List<DatasetTypeResponse>> response = controller.getDatasetTypes();

        List<DatasetTypeResponse> types = response.getBody();
        assertNotNull(types);

        // 创建期望的图标映射
        for (DatasetTypeResponse type : types) {
            String expectedIcon;
            switch (type.getCode()) {
                case "IMAGE":
                    expectedIcon = "🖼️";
                    break;
                case "TEXT":
                    expectedIcon = "📄";
                    break;
                case "AUDIO":
                    expectedIcon = "🎵";
                    break;
                case "VIDEO":
                    expectedIcon = "🎬";
                    break;
                case "MULTIMODAL":
                    expectedIcon = "📊";
                    break;
                default:
                    expectedIcon = "📁";
                    break;
            }
            assertEquals(expectedIcon, type.getIcon(), "Icon mismatch for type: " + type.getCode());
        }
    }

    @Test
    @DisplayName("datasetTypesGet: 验证特定格式包含")
    void getDatasetTypes_specificFormatInclusion() {
        ResponseEntity<List<DatasetTypeResponse>> response = controller.getDatasetTypes();

        List<DatasetTypeResponse> types = response.getBody();
        assertNotNull(types);

        // 验证IMAGE类型包含所有期望的格式
        DatasetTypeResponse imageType = types.stream()
                .filter(type -> "IMAGE".equals(type.getCode()))
                .findFirst()
                .orElse(null);
        assertNotNull(imageType);
        List<String> imageFormats = imageType.getSupportedFormats();
        assertTrue(imageFormats.contains("jpg"));
        assertTrue(imageFormats.contains("jpeg"));
        assertTrue(imageFormats.contains("png"));
        assertTrue(imageFormats.contains("bmp"));
        assertTrue(imageFormats.contains("gif"));
        assertEquals(5, imageFormats.size());

        // 验证TEXT类型包含所有期望的格式
        DatasetTypeResponse textType = types.stream()
                .filter(type -> "TEXT".equals(type.getCode()))
                .findFirst()
                .orElse(null);
        assertNotNull(textType);
        List<String> textFormats = textType.getSupportedFormats();
        assertTrue(textFormats.contains("txt"));
        assertTrue(textFormats.contains("csv"));
        assertTrue(textFormats.contains("json"));
        assertTrue(textFormats.contains("xml"));
        assertEquals(4, textFormats.size());

        // 验证MULTIMODAL类型包含通配符
        DatasetTypeResponse multimodalType = types.stream()
                .filter(type -> "MULTIMODAL".equals(type.getCode()))
                .findFirst()
                .orElse(null);
        assertNotNull(multimodalType);
        List<String> multimodalFormats = multimodalType.getSupportedFormats();
        assertTrue(multimodalFormats.contains("*"));
        assertEquals(1, multimodalFormats.size());
    }

    @Test
    @DisplayName("datasetTypesGet: 返回响应状态正确")
    void getDatasetTypes_responseStatus() {
        ResponseEntity<List<DatasetTypeResponse>> response = controller.getDatasetTypes();

        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
    }

    @Test
    @DisplayName("datasetTypesGet: 多次调用返回一致结果")
    void getDatasetTypes_consistentResults() {
        ResponseEntity<List<DatasetTypeResponse>> response1 = controller.getDatasetTypes();
        ResponseEntity<List<DatasetTypeResponse>> response2 = controller.getDatasetTypes();

        assertEquals(response1.getStatusCode(), response2.getStatusCode());
        assertEquals(response1.getBody().size(), response2.getBody().size());

        List<DatasetTypeResponse> types1 = response1.getBody();
        List<DatasetTypeResponse> types2 = response2.getBody();

        for (int i = 0; i < types1.size(); i++) {
            DatasetTypeResponse type1 = types1.get(i);
            DatasetTypeResponse type2 = types2.get(i);

            assertEquals(type1.getCode(), type2.getCode());
            assertEquals(type1.getName(), type2.getName());
            assertEquals(type1.getDescription(), type2.getDescription());
            assertEquals(type1.getIcon(), type2.getIcon());
            assertEquals(type1.getSupportedFormats(), type2.getSupportedFormats());
        }
    }
}
