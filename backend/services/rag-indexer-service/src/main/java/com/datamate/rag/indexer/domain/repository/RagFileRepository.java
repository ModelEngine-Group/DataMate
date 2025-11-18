package com.datamate.rag.indexer.domain.repository;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.rag.indexer.domain.model.RagFile;
import com.datamate.rag.indexer.interfaces.dto.RagFileReq;

import java.util.List;

/**
 * 知识库文件仓储接口
 *
 * @author dallas
 * @since 2025-10-24
 */
public interface RagFileRepository extends IRepository<RagFile> {
    void removeByKnowledgeBaseId(String knowledgeBaseId);

    List<RagFile> findNotSuccessByKnowledgeBaseId(String knowledgeBaseId);

    List<RagFile> findAllByKnowledgeBaseId(String knowledgeBaseId);

    IPage<RagFile> page(IPage<RagFile> page, RagFileReq request);
}
