package com.datamate.rag.indexer.application;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.datamate.rag.indexer.domain.model.FileStatus;
import com.datamate.rag.indexer.domain.model.KnowledgeBase;
import com.datamate.rag.indexer.domain.model.RagChunk;
import com.datamate.rag.indexer.domain.model.RagFile;
import com.datamate.rag.indexer.domain.repository.KnowledgeBaseRepository;
import com.datamate.rag.indexer.domain.repository.RagFileRepository;
import com.datamate.rag.indexer.infrastructure.event.DataInsertedEvent;
import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.KnowledgeBaseErrorCode;
import com.datamate.common.interfaces.PagedResponse;
import com.datamate.common.interfaces.PagingQuery;
import com.datamate.rag.indexer.interfaces.dto.*;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.BeanUtils;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

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
    public void update(String knowledgeBaseId, KnowledgeBaseUpdateReq request) {
        KnowledgeBase knowledgeBase = Optional.ofNullable(knowledgeBaseRepository.getById(knowledgeBaseId))
                .orElseThrow(() -> BusinessException.of(KnowledgeBaseErrorCode.KNOWLEDGE_BASE_NOT_FOUND));
        if (StringUtils.hasText(request.getName())) {
            knowledgeBase.setName(request.getName());
        }
        if (StringUtils.hasText(request.getDescription())) {
            knowledgeBase.setDescription(request.getDescription());
        }
        knowledgeBaseRepository.updateById(knowledgeBase);
    }

    public void delete(String knowledgeBaseId) {
        knowledgeBaseRepository.removeById(knowledgeBaseId);
        ragFileRepository.removeByKnowledgeBaseId(knowledgeBaseId);
        //  TODO: 删除知识库关联的所有文档
    }

    public KnowledgeBase getById(String knowledgeBaseId) {
        return Optional.ofNullable(knowledgeBaseRepository.getById(knowledgeBaseId))
                .orElseThrow(() -> BusinessException.of(KnowledgeBaseErrorCode.KNOWLEDGE_BASE_NOT_FOUND));
    }

    public PagedResponse<KnowledgeBase> list(KnowledgeBaseQueryReq request) {
        IPage<KnowledgeBase> page = new Page<>(request.getPage(), request.getSize());
        page = knowledgeBaseRepository.page(page, request);
        return PagedResponse.of(page.getRecords(), page.getCurrent(), page.getTotal(), page.getPages());
    }

    @Transactional(rollbackFor = Exception.class)
    public void addFiles(AddFilesReq request) {
        KnowledgeBase knowledgeBase = Optional.ofNullable(knowledgeBaseRepository.getById(request.getKnowledgeBaseId()))
                .orElseThrow(() -> BusinessException.of(KnowledgeBaseErrorCode.KNOWLEDGE_BASE_NOT_FOUND));
        List<RagFile> ragFiles = request.getFiles().stream().map(fileInfo -> {
            RagFile ragFile = new RagFile();
            ragFile.setKnowledgeBaseId(knowledgeBase.getId());
            ragFile.setFileId(fileInfo.id());
            ragFile.setFileName(fileInfo.name());
            ragFile.setStatus(FileStatus.UNPROCESSED);
            return ragFile;
        }).toList();
        ragFileRepository.saveBatch(ragFiles, 100);
        eventPublisher.publishEvent(new DataInsertedEvent(knowledgeBase, request.getProcessType()));
    }

    public PagedResponse<RagFile> listFiles(String knowledgeBaseId, RagFileReq request) {
        IPage<RagFile> page = new Page<>(request.getPage(), request.getSize());
        page = ragFileRepository.page(page);
        return PagedResponse.of(page.getRecords(), page.getCurrent(), page.getTotal(), page.getPages());
    }

    public void deleteFiles(String knowledgeBaseId, DeleteFilesReq request) {
        ragFileRepository.removeByIds(request.getIds());
    }

    public PagedResponse<RagChunk> getChunks(String knowledgeBaseId, String ragFileId, PagingQuery pagingQuery) {
        IPage<RagChunk> page = new Page<>(pagingQuery.getPage(), pagingQuery.getSize());
        return PagedResponse.of(page.getRecords(), page.getCurrent(), page.getTotal(), page.getPages());
    }
}