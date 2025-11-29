package com.datamate.rag.indexer.application;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.KnowledgeBaseErrorCode;
import com.datamate.common.interfaces.PagedResponse;
import com.datamate.common.interfaces.PagingQuery;
import com.datamate.common.setting.domain.entity.ModelConfig;
import com.datamate.common.setting.domain.repository.ModelConfigRepository;
import com.datamate.common.setting.infrastructure.client.ModelClient;
import com.datamate.rag.indexer.domain.model.FileStatus;
import com.datamate.rag.indexer.domain.model.KnowledgeBase;
import com.datamate.rag.indexer.domain.model.RagChunk;
import com.datamate.rag.indexer.domain.model.RagFile;
import com.datamate.rag.indexer.domain.repository.KnowledgeBaseRepository;
import com.datamate.rag.indexer.domain.repository.RagFileRepository;
import com.datamate.rag.indexer.infrastructure.event.DataInsertedEvent;
import com.datamate.rag.indexer.infrastructure.milvus.MilvusService;
import com.datamate.rag.indexer.interfaces.dto.*;
import dev.langchain4j.data.embedding.Embedding;
import dev.langchain4j.model.embedding.EmbeddingModel;
import io.milvus.v2.service.collection.request.DropCollectionReq;
import io.milvus.v2.service.collection.request.RenameCollectionReq;
import io.milvus.v2.service.vector.request.DeleteReq;
import io.milvus.v2.service.vector.request.QueryReq;
import io.milvus.v2.service.vector.response.QueryResp;
import io.milvus.v2.service.vector.response.SearchResp;
import lombok.RequiredArgsConstructor;
import org.jetbrains.annotations.NotNull;
import org.springframework.beans.BeanUtils;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.Collections;
import java.util.List;
import java.util.Optional;

/**
 * 知识库服务类
 *
 * @author dallas
 * @since 2025-10-24
 */
@Service
@RequiredArgsConstructor
public class KnowledgeBaseService {
    private final KnowledgeBaseRepository knowledgeBaseRepository;
    private final RagFileRepository ragFileRepository;
    private final ApplicationEventPublisher eventPublisher;
    private final ModelConfigRepository modelConfigRepository;
    private final MilvusService milvusService;

    /**
     * 创建知识库
     *
     * @param request 知识库创建请求
     * @return 知识库 ID
     */
    public String create(KnowledgeBaseCreateReq request) {
        KnowledgeBase knowledgeBase = new KnowledgeBase();
        BeanUtils.copyProperties(request, knowledgeBase);
        knowledgeBaseRepository.save(knowledgeBase);
        return knowledgeBase.getId();
    }

    /**
     * 更新知识库
     *
     * @param knowledgeBaseId 知识库 ID
     * @param request         知识库更新请求
     */
    @Transactional(rollbackFor = Exception.class)
    public void update(String knowledgeBaseId, KnowledgeBaseUpdateReq request) {
        KnowledgeBase knowledgeBase = Optional.ofNullable(knowledgeBaseRepository.getById(knowledgeBaseId))
                .orElseThrow(() -> BusinessException.of(KnowledgeBaseErrorCode.KNOWLEDGE_BASE_NOT_FOUND));
        if (StringUtils.hasText(request.getName()) && !knowledgeBase.getName().equals(request.getName())) {
            milvusService.getMilvusClient().renameCollection(RenameCollectionReq.builder()
                    .collectionName(knowledgeBase.getName())
                    .newCollectionName(request.getName())
                    .build());
            knowledgeBase.setName(request.getName());
        }
        knowledgeBase.setDescription(request.getDescription());
        knowledgeBaseRepository.updateById(knowledgeBase);
    }


    /**
     * 删除知识库
     *
     * @param knowledgeBaseId 知识库 ID
     */
    @Transactional(rollbackFor = Exception.class)
    public void delete(String knowledgeBaseId) {
        KnowledgeBase knowledgeBase = Optional.ofNullable(knowledgeBaseRepository.getById(knowledgeBaseId))
                .orElseThrow(() -> BusinessException.of(KnowledgeBaseErrorCode.KNOWLEDGE_BASE_NOT_FOUND));
        knowledgeBaseRepository.removeById(knowledgeBaseId);
        ragFileRepository.removeByKnowledgeBaseId(knowledgeBaseId);
        milvusService.getMilvusClient().dropCollection(DropCollectionReq.builder().collectionName(knowledgeBase.getName()).build());
    }

    public KnowledgeBaseResp getById(String knowledgeBaseId) {
        KnowledgeBase knowledgeBase = Optional.ofNullable(knowledgeBaseRepository.getById(knowledgeBaseId))
                .orElseThrow(() -> BusinessException.of(KnowledgeBaseErrorCode.KNOWLEDGE_BASE_NOT_FOUND));
        KnowledgeBaseResp resp = getKnowledgeBaseResp(knowledgeBase);
        resp.setEmbedding(modelConfigRepository.getById(knowledgeBase.getEmbeddingModel()));
        resp.setChat(modelConfigRepository.getById(knowledgeBase.getChatModel()));
        return resp;
    }

    @NotNull
    private KnowledgeBaseResp getKnowledgeBaseResp(KnowledgeBase knowledgeBase) {
        KnowledgeBaseResp resp = new KnowledgeBaseResp();
        BeanUtils.copyProperties(knowledgeBase, resp);

        // 获取该知识库的所有文件
        List<RagFile> files = ragFileRepository.findAllByKnowledgeBaseId(knowledgeBase.getId());
        resp.setFileCount((long) files.size());

        // 计算分片总数
        long totalChunkCount = files.stream()
                .mapToLong(file -> file.getChunkCount() != null ? file.getChunkCount() : 0)
                .sum();
        resp.setChunkCount(totalChunkCount);
        return resp;
    }

    public PagedResponse<KnowledgeBaseResp> list(KnowledgeBaseQueryReq request) {
        IPage<KnowledgeBase> page = new Page<>(request.getPage(), request.getSize());
        page = knowledgeBaseRepository.page(page, request);

        // 将 KnowledgeBase 转换为 KnowledgeBaseResp，并计算 fileCount 和 chunkCount
        List<KnowledgeBaseResp> respList = page.getRecords().stream().map(this::getKnowledgeBaseResp).toList();
        return PagedResponse.of(respList, page.getCurrent(), page.getTotal(), page.getPages());
    }

    @Transactional(rollbackFor = Exception.class)
    public void addFiles(AddFilesReq request) {
        KnowledgeBase knowledgeBase = Optional.ofNullable(knowledgeBaseRepository.getById(request.getKnowledgeBaseId()))
                .orElseThrow(() -> BusinessException.of(KnowledgeBaseErrorCode.KNOWLEDGE_BASE_NOT_FOUND));
        List<RagFile> ragFiles = request.getFiles().stream().map(fileInfo -> {
            RagFile ragFile = new RagFile();
            ragFile.setKnowledgeBaseId(knowledgeBase.getId());
            ragFile.setFileId(fileInfo.id());
            ragFile.setFileName(fileInfo.fileName());
            ragFile.setStatus(FileStatus.UNPROCESSED);
            return ragFile;
        }).toList();
        ragFileRepository.saveBatch(ragFiles, 100);
        eventPublisher.publishEvent(new DataInsertedEvent(knowledgeBase, request));
    }

    public PagedResponse<RagFile> listFiles(String knowledgeBaseId, RagFileReq request) {
        IPage<RagFile> page = new Page<>(request.getPage(), request.getSize());
        request.setKnowledgeBaseId(knowledgeBaseId);
        page = ragFileRepository.page(page, request);
        return PagedResponse.of(page.getRecords(), page.getCurrent(), page.getTotal(), page.getPages());
    }

    @Transactional(rollbackFor = Exception.class)
    public void deleteFiles(String knowledgeBaseId, DeleteFilesReq request) {
        KnowledgeBase knowledgeBase = Optional.ofNullable(knowledgeBaseRepository.getById(knowledgeBaseId))
                .orElseThrow(() -> BusinessException.of(KnowledgeBaseErrorCode.KNOWLEDGE_BASE_NOT_FOUND));
        ragFileRepository.removeByIds(request.getIds());
        milvusService.getMilvusClient().delete(DeleteReq.builder()
                .collectionName(knowledgeBase.getName())
                .filter("metadata[\"rag_file_id\"] in [" + org.apache.commons.lang3.StringUtils.join(request.getIds().stream().map(id -> "\"" + id + "\"").toArray(), ",") + "]")
                .build());
    }

    public PagedResponse<RagChunk> getChunks(String knowledgeBaseId, String ragFileId, PagingQuery pagingQuery) {
        KnowledgeBase knowledgeBase = Optional.ofNullable(knowledgeBaseRepository.getById(knowledgeBaseId))
                .orElseThrow(() -> BusinessException.of(KnowledgeBaseErrorCode.KNOWLEDGE_BASE_NOT_FOUND));
        QueryResp results = milvusService.getMilvusClient().query(QueryReq.builder()
                .collectionName(knowledgeBase.getName())
                .filter("metadata[\"rag_file_id\"] == \"" + ragFileId + "\"")
                .outputFields(Collections.singletonList("*"))
                .limit(Long.valueOf(pagingQuery.getSize()))
                .offset((long) (pagingQuery.getPage() - 1) * pagingQuery.getSize())
                .build());
        List<QueryResp.QueryResult> queryResults = results.getQueryResults();
        List<RagChunk> ragChunks = queryResults.stream()
                .map(QueryResp.QueryResult::getEntity)
                .map(item -> new RagChunk(
                        item.get("id").toString(),
                        item.get("text").toString(),
                        item.get("metadata").toString()
                )).toList();

        // 获取总数
        QueryResp countResults = milvusService.getMilvusClient().query(QueryReq.builder()
                .collectionName(knowledgeBase.getName())
                .filter("metadata[\"rag_file_id\"] == \"" + ragFileId + "\"")
                .outputFields(Collections.singletonList("count(*)"))
                .build());

        long totalCount = Long.parseLong(countResults.getQueryResults().getFirst().getEntity().get("count(*)").toString());
        return PagedResponse.of(ragChunks, pagingQuery.getPage(), totalCount, (int) Math.ceil((double) totalCount / pagingQuery.getSize()));
    }

    /**
     * 检索知识库内容
     *
     * @param request 检索请求
     * @return 检索结果
     */
    public List<SearchResp.SearchResult> retrieve(RetrieveReq request) {
        KnowledgeBase knowledgeBase = Optional.ofNullable(knowledgeBaseRepository.getById(request.getKnowledgeBaseIds().getFirst()))
                .orElseThrow(() -> BusinessException.of(KnowledgeBaseErrorCode.KNOWLEDGE_BASE_NOT_FOUND));
        ModelConfig modelConfig = modelConfigRepository.getById(knowledgeBase.getEmbeddingModel());
        EmbeddingModel embeddingModel = ModelClient.invokeEmbeddingModel(modelConfig);
        Embedding embedding = embeddingModel.embed(request.getQuery()).content();
        SearchResp searchResp = milvusService.hybridSearch(knowledgeBase.getName(), request.getQuery(), embedding.vector(), request.getTopK());
        List<SearchResp.SearchResult> searchResults = searchResp.getSearchResults().getFirst();

        searchResults.forEach(item -> {
            String metadata = item.getEntity().get("metadata").toString();
            item.getEntity().put("metadata", metadata);
        });
        return searchResults;
    }
}