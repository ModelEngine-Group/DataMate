package com.datamate.rag.indexer.infrastructure.milvus;

import com.google.gson.*;
import dev.langchain4j.data.embedding.Embedding;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.store.embedding.EmbeddingStore;
import dev.langchain4j.store.embedding.milvus.MilvusEmbeddingStore;
import io.milvus.common.clientenum.FunctionType;
import io.milvus.v2.client.ConnectConfig;
import io.milvus.v2.client.MilvusClientV2;
import io.milvus.v2.common.DataType;
import io.milvus.v2.common.IndexParam;
import io.milvus.v2.service.collection.request.AddFieldReq;
import io.milvus.v2.service.collection.request.CreateCollectionReq;
import io.milvus.v2.service.collection.request.HasCollectionReq;
import io.milvus.v2.service.vector.request.AnnSearchReq;
import io.milvus.v2.service.vector.request.FunctionScore;
import io.milvus.v2.service.vector.request.HybridSearchReq;
import io.milvus.v2.service.vector.request.InsertReq;
import io.milvus.v2.service.vector.request.data.BaseVector;
import io.milvus.v2.service.vector.request.data.EmbeddedText;
import io.milvus.v2.service.vector.request.data.FloatVec;
import io.milvus.v2.service.vector.response.SearchResp;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.*;

import static dev.langchain4j.internal.Utils.randomUUID;

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
    @Value("${datamate.rag.milvus-uri:http://milvus-standalone:19530}")
    private String milvusUri;
    private static final Gson GSON;

    static {
        GSON = (new GsonBuilder()).setObjectToNumberStrategy(ToNumberPolicy.LONG_OR_DOUBLE).create();
    }

    private volatile MilvusClientV2 milvusClient;

    public EmbeddingStore<TextSegment> embeddingStore(EmbeddingModel embeddingModel, String knowledgeBaseName) {
        return MilvusEmbeddingStore.builder()
                .uri(milvusUri)
                .collectionName(knowledgeBaseName)
                .dimension(embeddingModel.dimension())
                .build();
    }

    /**
     * 单例模式获取 Milvus 客户端，不依赖 Spring 容器
     *
     * @return MilvusClient
     */
    public MilvusClientV2 getMilvusClient() {
        if (milvusClient == null) {
            synchronized (this) {
                if (milvusClient == null) {
                    try {
                        ConnectConfig connectConfig = ConnectConfig.builder()
                                .uri(milvusUri)
                                .build();
                        milvusClient = new MilvusClientV2(connectConfig);
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


    public boolean hasCollection(String collectionName) {
        HasCollectionReq request = HasCollectionReq.builder().collectionName(collectionName).build();
        return getMilvusClient().hasCollection(request);
    }

    public void createCollection(String collectionName, int dimension) {
        CreateCollectionReq.CollectionSchema schema = CreateCollectionReq.CollectionSchema.builder()
                .build();
        schema.addField(AddFieldReq.builder()
                .fieldName("id")
                .dataType(DataType.VarChar)
                .maxLength(36)
                .isPrimaryKey(true)
                .autoID(false)
                .build());
        schema.addField(AddFieldReq.builder()
                .fieldName("text")
                .dataType(DataType.VarChar)
                .maxLength(65535)
                .enableAnalyzer(true)
                .build());
        schema.addField(AddFieldReq.builder()
                .fieldName("metadata")
                .dataType(DataType.JSON)
                .build());
        schema.addField(AddFieldReq.builder()
                .fieldName("vector")
                .dataType(DataType.FloatVector)
                .dimension(dimension)
                .build());
        schema.addField(AddFieldReq.builder()
                .fieldName("sparse")
                .dataType(DataType.SparseFloatVector)
                .build());
        schema.addFunction(CreateCollectionReq.Function.builder()
                .functionType(FunctionType.BM25)
                .name("text_bm25_emb")
                .inputFieldNames(Collections.singletonList("text"))
                .outputFieldNames(Collections.singletonList("sparse"))
                .build());

        Map<String, Object> params = new HashMap<>();
        params.put("inverted_index_algo", "DAAT_MAXSCORE");
        params.put("bm25_k1", 1.2);
        params.put("bm25_b", 0.75);

        List<IndexParam> indexes = new ArrayList<>();
        indexes.add(IndexParam.builder()
                .fieldName("sparse")
                .indexType(IndexParam.IndexType.SPARSE_INVERTED_INDEX)
                .metricType(IndexParam.MetricType.BM25)
                .extraParams(params)
                .build());
        indexes.add(IndexParam.builder()
                .fieldName("vector")
                .indexType(IndexParam.IndexType.FLAT)
                .metricType(IndexParam.MetricType.COSINE)
                .extraParams(Map.of())
                .build());

        CreateCollectionReq createCollectionReq = CreateCollectionReq.builder()
                .collectionName(collectionName)
                .collectionSchema(schema)
                .indexParams(indexes)
                .build();
        this.getMilvusClient().createCollection(createCollectionReq);
    }

    public void addAll(String collectionName, List<TextSegment> textSegments, List<Embedding> embeddings) {
        List<JsonObject> data = convertToJsonObjects(textSegments, embeddings);
        InsertReq insertReq = InsertReq.builder()
                .collectionName(collectionName)
                .data(data)
                .build();
        this.getMilvusClient().insert(insertReq);
    }

    public List<JsonObject> convertToJsonObjects(List<TextSegment> textSegments, List<Embedding> embeddings) {
        List<JsonObject> data = new ArrayList<>();
        for (int i = 0; i < textSegments.size(); i++) {
            JsonObject jsonObject = new JsonObject();
            jsonObject.addProperty("id", randomUUID());
            jsonObject.addProperty("text", textSegments.get(i).text());
            jsonObject.add("metadata", GSON.toJsonTree(textSegments.get(i).metadata().toMap()).getAsJsonObject());
            JsonArray vectorArray = new JsonArray();
            for (float f : embeddings.get(i).vector()) {
                vectorArray.add(f);
            }
            jsonObject.add("vector", vectorArray);
            data.add(jsonObject);
        }
        return data;
    }

    public SearchResp hybridSearch(String collectionName, String query, float[] queryDense, int topK) {
        List<BaseVector> queryTexts = Collections.singletonList(new EmbeddedText(query));
        List<BaseVector> queryVectors = Collections.singletonList(new FloatVec(queryDense));

        List<AnnSearchReq> searchRequests = new ArrayList<>();
        searchRequests.add(AnnSearchReq.builder()
                .vectorFieldName("vector")
                .vectors(queryVectors)
                .params("{\"nprobe\": 10}")
                .topK(topK)
                .build());
        searchRequests.add(AnnSearchReq.builder()
                .vectorFieldName("sparse")
                .vectors(queryTexts)
                .params("{\"drop_ratio_search\": 0.2}")
                .topK(topK)
                .build());

        CreateCollectionReq.Function ranker = CreateCollectionReq.Function.builder()
                .name("weight")
                .functionType(FunctionType.RERANK)
                .param("reranker", "weighted")
                .param("weights", "[0.1, 0.9]")
                .param("norm_score", "true")
                .build();

        FunctionScore functionScore = FunctionScore.builder()
                .functions(Collections.singletonList(ranker))
                .build();


        SearchResp searchResp = this.getMilvusClient().hybridSearch(HybridSearchReq.builder()
                .collectionName(collectionName)
                .searchRequests(searchRequests)
                .functionScore(functionScore)
                .outFields(Arrays.asList("id", "text", "metadata"))
                .limit(topK)
                .build());
        return searchResp;
    }
}
