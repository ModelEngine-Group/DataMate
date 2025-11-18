package com.datamate.rag.indexer.infrastructure.persistence.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.rag.indexer.domain.model.FileStatus;
import com.datamate.rag.indexer.domain.model.RagFile;
import com.datamate.rag.indexer.domain.repository.RagFileRepository;
import com.datamate.rag.indexer.infrastructure.persistence.mapper.RagFileMapper;
import com.datamate.rag.indexer.interfaces.dto.RagFileReq;
import org.springframework.stereotype.Repository;
import org.springframework.util.StringUtils;

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
    public List<RagFile> findNotSuccessByKnowledgeBaseId(String knowledgeBaseId) {
        return lambdaQuery()
                .eq(RagFile::getKnowledgeBaseId, knowledgeBaseId)
                .in(RagFile::getStatus, FileStatus.UNPROCESSED, FileStatus.PROCESS_FAILED)
                .list();
    }

    @Override
    public List<RagFile> findAllByKnowledgeBaseId(String knowledgeBaseId) {
        return lambdaQuery()
                .eq(RagFile::getKnowledgeBaseId, knowledgeBaseId)
                .list();
    }

    @Override
    public IPage<RagFile> page(IPage<RagFile> page, RagFileReq request) {
        return lambdaQuery()
                .eq(RagFile::getKnowledgeBaseId, request.getKnowledgeBaseId())
                .like(StringUtils.hasText(request.getFileName()), RagFile::getFileName, request.getFileName())
                .page(page);
    }
}
