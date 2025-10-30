package com.datamate.rag.indexer.domain.repository;

import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.rag.indexer.domain.model.RagFile;

import java.util.List;

/**
 * 知识库文件仓储接口
 *
 * @author dallas
 * @since 2025-10-24
 */
public interface RagFileRepository extends IRepository<RagFile> {
    void removeByKnowledgeBaseId(String knowledgeBaseId);

    List<RagFile> findByKnowledgeBaseId(String knowledgeBaseId);
}
