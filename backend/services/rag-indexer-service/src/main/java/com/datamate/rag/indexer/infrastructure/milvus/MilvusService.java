package com.datamate.rag.indexer.infrastructure.milvus;

import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.store.embedding.EmbeddingStore;
import dev.langchain4j.store.embedding.milvus.MilvusEmbeddingStore;
import io.milvus.client.MilvusClient;
import io.milvus.client.MilvusServiceClient;
import io.milvus.param.ConnectParam;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Milvus 服务类
 *
 * @author dallas
 * @since 2025-11-17
 */
@Slf4j
@Component
public class MilvusService {
    @Value("${datamate.rag.milvus-host:milvus}")
    private String milvusHost;
    @Value("${datamate.rag.milvus-port:19530}")
    private int milvusPort;

    private volatile MilvusClient milvusClient;

    public EmbeddingStore<TextSegment> embeddingStore(EmbeddingModel embeddingModel, String knowledgeBaseName) {
        return MilvusEmbeddingStore.builder()
                .host(milvusHost)
                .port(milvusPort)
                .collectionName(knowledgeBaseName)
                .dimension(embeddingModel.dimension())
                .build();
    }

    public MilvusClient getMilvusClient() {
        if (milvusClient == null) {
            synchronized (this) {
                if (milvusClient == null) {
                    try {
                        ConnectParam connectParam = ConnectParam.newBuilder()
                                .withHost(milvusHost)
                                .withPort(milvusPort)
                                .build();
                        milvusClient = new MilvusServiceClient(connectParam);
                        log.info("Milvus client connected successfully");
                    } catch (Exception e) {
                        log.error("Milvus client connection failed: {}", e.getMessage());
                        throw new RuntimeException("Milvus client connection failed", e);
                    }
                }
            }
        }
        return milvusClient;
    }
}
