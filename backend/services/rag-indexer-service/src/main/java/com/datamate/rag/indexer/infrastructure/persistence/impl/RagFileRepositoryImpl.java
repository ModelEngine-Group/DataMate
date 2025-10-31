package com.datamate.rag.indexer.infrastructure.persistence.impl;

import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.rag.indexer.domain.model.FileStatus;
import com.datamate.rag.indexer.domain.model.RagFile;
import com.datamate.rag.indexer.domain.repository.RagFileRepository;
import com.datamate.rag.indexer.infrastructure.persistence.mapper.RagFileMapper;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 知识库文件仓储实现类
 *
 * @author dallas
 * @since 2025-10-24
 */
@Repository
public class RagFileRepositoryImpl extends CrudRepository<RagFileMapper, RagFile> implements RagFileRepository {
    @Override
    public void removeByKnowledgeBaseId(String knowledgeBaseId) {
        lambdaUpdate().eq(RagFile::getKnowledgeBaseId, knowledgeBaseId).remove();
    }

    @Override
    public List<RagFile> findByKnowledgeBaseId(String knowledgeBaseId) {
        return lambdaQuery()
                .eq(RagFile::getKnowledgeBaseId, knowledgeBaseId)
                .in(RagFile::getStatus, FileStatus.UNPROCESSED, FileStatus.PROCESS_FAILED)
                .list();
    }
}
