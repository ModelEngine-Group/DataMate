package com.datamate.rag.indexer.infrastructure.persistence.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.rag.indexer.domain.model.KnowledgeBase;
import com.datamate.rag.indexer.domain.repository.KnowledgeBaseRepository;
import com.datamate.rag.indexer.infrastructure.persistence.mapper.KnowledgeBaseMapper;
import com.datamate.rag.indexer.interfaces.dto.KnowledgeBaseQueryReq;
import org.springframework.stereotype.Repository;
import org.springframework.util.StringUtils;

/**
 * 知识库仓储实现类
 *
 * @author dallas
 * @since 2025-10-24
 */
@Repository
public class KnowledgeBaseRepositoryImpl extends CrudRepository<KnowledgeBaseMapper, KnowledgeBase> implements KnowledgeBaseRepository {

    @Override
    public IPage<KnowledgeBase> page(IPage<KnowledgeBase> page, KnowledgeBaseQueryReq request) {
        return this.page(page, new LambdaQueryWrapper<KnowledgeBase>()
                .like(StringUtils.hasText(request.getName()), KnowledgeBase::getName, request.getName())
                .like(StringUtils.hasText(request.getDescription()), KnowledgeBase::getDescription, request.getDescription())
                .like(StringUtils.hasText(request.getCreatedBy()), KnowledgeBase::getCreatedBy, request.getCreatedBy())
                .like(StringUtils.hasText(request.getUpdatedBy()), KnowledgeBase::getUpdatedBy, request.getUpdatedBy())
                .orderByDesc(KnowledgeBase::getCreatedAt));
    }
}
