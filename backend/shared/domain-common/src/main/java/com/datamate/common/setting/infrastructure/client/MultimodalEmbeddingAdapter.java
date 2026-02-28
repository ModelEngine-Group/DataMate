package com.datamate.common.setting.infrastructure.client;

import dev.langchain4j.data.embedding.Embedding;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.model.output.Response;
import lombok.extern.slf4j.Slf4j;

import java.util.List;

/**
 * 多模态嵌入模型适配器，将 MultimodalEmbeddingClient 适配为 EmbeddingModel 接口。
 * 用于在 RAG 流程中支持多模态 embedding 模型。
 *
 * @author datamate
 * @since 2025-02-28
 */
@Slf4j
public class MultimodalEmbeddingAdapter implements EmbeddingModel {

    private final MultimodalEmbeddingClient client;
    private final int dimension;

    public MultimodalEmbeddingAdapter(String baseUrl, String apiKey, String modelName) {
        this.client = new MultimodalEmbeddingClient(baseUrl, apiKey, modelName);
        this.dimension = estimateDimension();
    }

    /**
     * 通过一次嵌入调用估算向量维度
     */
    private int estimateDimension() {
        try {
            float[] embedding = client.embedText("test");
            return embedding.length;
        } catch (Exception e) {
            log.warn("Failed to estimate embedding dimension, using default 1024", e);
            return 1024;
        }
    }

    @Override
    public Response<Embedding> embed(String text) {
        float[] vector = client.embedText(text);
        return Response.from(Embedding.from(vector));
    }

    @Override
    public Response<Embedding> embed(TextSegment textSegment) {
        return embed(textSegment.text());
    }

    @Override
    public Response<List<Embedding>> embedAll(List<TextSegment> textSegments) {
        List<Embedding> embeddings = textSegments.stream()
                .map(segment -> {
                    float[] vector = client.embedText(segment.text());
                    return Embedding.from(vector);
                })
                .toList();
        return Response.from(embeddings);
    }

    @Override
    public int dimension() {
        return dimension;
    }
}
