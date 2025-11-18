package com.datamate.rag.indexer.infrastructure.milvus;

import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.store.embedding.EmbeddingStore;
import dev.langchain4j.store.embedding.milvus.MilvusEmbeddingStore;
import io.milvus.client.MilvusClient;
import io.milvus.client.MilvusServiceClient;
import io.milvus.param.ConnectParam;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;

/**
 * Milvus 服务类
 *
 * @author dallas
 * @since 2025-11-17
 */
@Component
public class MilvusService {
    @Value("${datamate.rag.milvus-host:milvus-standalone}")
    private String milvusHost;
    @Value("${datamate.rag.milvus-port:19530}")
    private int milvusPort;

    public EmbeddingStore<TextSegment> embeddingStore(EmbeddingModel embeddingModel, String knowledgeBaseName) {
        return MilvusEmbeddingStore.builder()
                .host(milvusHost)
                .port(milvusPort)
                .collectionName(knowledgeBaseName)
                .dimension(embeddingModel.dimension())
                .build();
    }

    @Bean
    public MilvusClient milvusClient() {
        ConnectParam connectParam = ConnectParam.newBuilder()
                .withHost(milvusHost)
                .withPort(milvusPort)
                .build();
        return new MilvusServiceClient(connectParam);
    }
}
