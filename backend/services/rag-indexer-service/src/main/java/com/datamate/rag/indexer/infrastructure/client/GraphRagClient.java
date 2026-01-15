package com.datamate.rag.indexer.infrastructure.client;

import com.datamate.common.infrastructure.common.Response;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;

/**
 * 知识图谱RAG客户端
 *
 * @author dallas
 * @since 2026-01-15
 */
@FeignClient(name = "rag-service", url = "${collection.service.url:http://datamate-backend-python:18000}")
public interface GraphRagClient {
    /**
     * 启动知识图谱RAG任务
     * @param knowledgeBaseId 知识库ID
     * @return 任务详情
     */
    @PostMapping("/api/rag/process/{id}")
    Response<?> startGraphRagTask(@PathVariable("id") String knowledgeBaseId);
}
