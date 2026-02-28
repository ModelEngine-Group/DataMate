package com.datamate.common.setting.infrastructure.client;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

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

    /**
     * 根据 baseUrl 检测 API 端点
     */
    private String detectApiEndpoint() {
        if (isDashScope) {
            // 阿里云百炼：使用专用多模态端点
            return "https://dashscope.aliyuncs.com/api/v1/services/embeddings/multimodal-embedding/multimodal-embedding";
        }
        // 其他提供商：假设使用标准 /embeddings 端点
        return baseUrl + "/embeddings";
    }

    /**
     * 对纯文本进行嵌入
     */
    public float[] embedText(String text) {
        Map<String, Object> content = new HashMap<>();
        content.put("text", text);
        return embed(List.of(content));
    }

    /**
     * 对图像进行嵌入
     */
    public float[] embedImage(String imageUrl, String text) {
        Map<String, Object> content = new HashMap<>();
        content.put("image", imageUrl);
        if (text != null && !text.isEmpty()) {
            content.put("text", text);
        }
        return embed(List.of(content));
    }

    /**
     * 通用嵌入方法
     */
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

            // 尝试阿里云百炼格式: output.embeddings[0].embedding
            JsonNode outputNode = responseJson.path("output");
            if (!outputNode.isMissingNode()) {
                JsonNode embeddingsArray = outputNode.path("embeddings");
                if (embeddingsArray.isArray() && embeddingsArray.size() > 0) {
                    JsonNode embeddingNode = embeddingsArray.get(0).path("embedding");
                    return extractEmbedding(embeddingNode);
                }
            }

            // 尝试通用格式: data[0].embedding
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

    /**
     * 构建请求体
     */
    private Map<String, Object> buildRequestBody(List<Map<String, Object>> contents) {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("model", modelName);

        if (isDashScope) {
            // 阿里云百炼 HTTP API 格式: input.contents
            Map<String, Object> input = new HashMap<>();
            input.put("contents", contents);
            requestBody.put("input", input);
            requestBody.put("parameters", new HashMap<>());
        } else {
            // 通用格式: input 数组
            requestBody.put("input", contents);
        }

        return requestBody;
    }

    /**
     * 从 JSON 节点提取嵌入向量
     */
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

    /**
     * 健康检查：对测试文本进行嵌入
     */
    public void checkHealth() {
        embedText("health check");
        log.info("Multimodal embedding model health check passed: {}", modelName);
    }
}
