package com.datamate.common.setting.infrastructure.client;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 多模态嵌入模型客户端，支持文本和图像的嵌入。
 * 用于处理不支持 OpenAI 兼容模式的多模态 embedding 模型（如 qwen3-vl-embedding）。
 *
 * @author datamate
 * @since 2025-02-28
 */
@Slf4j
public class MultimodalEmbeddingClient {

    private final String baseUrl;
    private final String apiKey;
    private final String modelName;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final String apiEndpoint;
    private final boolean isDashScope;

    public MultimodalEmbeddingClient(String baseUrl, String apiKey, String modelName) {
        this.baseUrl = baseUrl.replaceAll("/$", "");
        this.apiKey = apiKey;
        this.modelName = modelName;
        this.restTemplate = new RestTemplate();
        this.objectMapper = new ObjectMapper();
        this.isDashScope = baseUrl.contains("dashscope.aliyuncs.com");
        this.apiEndpoint = detectApiEndpoint();
    }

    private String detectApiEndpoint() {
        if (isDashScope) {
            return "https://dashscope.aliyuncs.com/api/v1/services/embeddings/multimodal-embedding/multimodal-embedding";
        }
        return baseUrl + "/embeddings";
    }

    public float[] embedText(String text) {
        Map<String, Object> content = new HashMap<>();
        content.put("text", text);
        return embed(List.of(content));
    }

    public float[] embedImage(String imageUrl, String text) {
        Map<String, Object> content = new HashMap<>();
        content.put("image", convertToDataUrl(imageUrl));
        if (text != null && !text.isEmpty()) {
            content.put("text", text);
        }
        return embed(List.of(content));
    }

    /**
     * 将图片路径或URL转换为Data URL格式
     */
    private String convertToDataUrl(String imageInput) {
        if (imageInput == null || imageInput.isEmpty()) {
            throw new IllegalArgumentException("Image input cannot be null or empty");
        }

        if (imageInput.startsWith("http://") || imageInput.startsWith("https://") || imageInput.startsWith("data:")) {
            return imageInput;
        }

        Path imagePath = Path.of(imageInput);
        if (!Files.exists(imagePath)) {
            throw new RuntimeException("Image file not found: " + imageInput);
        }

        try {
            String mimeType = detectMimeType(imagePath);
            byte[] imageBytes = Files.readAllBytes(imagePath);
            String base64 = Base64.getEncoder().encodeToString(imageBytes);
            return "data:" + mimeType + ";base64," + base64;
        } catch (IOException e) {
            throw new RuntimeException("Failed to read image file: " + imageInput, e);
        }
    }

    /**
     * 根据文件扩展名检测 MIME 类型
     */
    private String detectMimeType(Path imagePath) {
        String fileName = imagePath.getFileName().toString().toLowerCase();
        if (fileName.endsWith(".jpg") || fileName.endsWith(".jpeg")) {
            return "image/jpeg";
        } else if (fileName.endsWith(".png")) {
            return "image/png";
        } else if (fileName.endsWith(".gif")) {
            return "image/gif";
        } else if (fileName.endsWith(".bmp")) {
            return "image/bmp";
        } else if (fileName.endsWith(".webp")) {
            return "image/webp";
        } else if (fileName.endsWith(".svg")) {
            return "image/svg+xml";
        } else if (fileName.endsWith(".tiff") || fileName.endsWith(".tif")) {
            return "image/tiff";
        }
        return "image/jpeg";
    }

    private float[] embed(List<Map<String, Object>> contents) {
        Map<String, Object> requestBody = buildRequestBody(contents);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setBearerAuth(apiKey);

        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

        try {
            ResponseEntity<String> response = restTemplate.exchange(
                    apiEndpoint,
                    HttpMethod.POST,
                    entity,
                    String.class
            );

            if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
                throw new RuntimeException("Embedding API call failed: " + response.getStatusCode());
            }

            JsonNode responseJson = objectMapper.readTree(response.getBody());

            JsonNode outputNode = responseJson.path("output");
            if (!outputNode.isMissingNode()) {
                JsonNode embeddingsArray = outputNode.path("embeddings");
                if (embeddingsArray.isArray() && embeddingsArray.size() > 0) {
                    JsonNode embeddingNode = embeddingsArray.get(0).path("embedding");
                    return extractEmbedding(embeddingNode);
                }
            }

            JsonNode dataArray = responseJson.path("data");
            if (dataArray.isArray() && dataArray.size() > 0) {
                JsonNode embeddingNode = dataArray.get(0).path("embedding");
                return extractEmbedding(embeddingNode);
            }

            throw new RuntimeException("Invalid response format: missing embedding data");
        } catch (Exception e) {
            throw new RuntimeException("Embedding API call failed: " + e.getMessage(), e);
        }
    }

    private Map<String, Object> buildRequestBody(List<Map<String, Object>> contents) {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("model", modelName);

        if (isDashScope) {
            Map<String, Object> input = new HashMap<>();
            input.put("contents", contents);
            requestBody.put("input", input);
            requestBody.put("parameters", new HashMap<>());
        } else {
            requestBody.put("input", contents);
        }

        return requestBody;
    }

    private float[] extractEmbedding(JsonNode embeddingNode) {
        if (embeddingNode.isMissingNode() || !embeddingNode.isArray()) {
            throw new RuntimeException("Invalid response format: embedding is not an array");
        }
        float[] embedding = new float[embeddingNode.size()];
        for (int i = 0; i < embeddingNode.size(); i++) {
            embedding[i] = (float) embeddingNode.get(i).asDouble();
        }
        return embedding;
    }

    public void checkHealth() {
        embedText("health check");
        log.info("Multimodal embedding model health check passed: {}", modelName);
    }
}
