package com.datamate.rag.indexer.domain.repository;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.rag.indexer.domain.model.KnowledgeBase;
import com.datamate.rag.indexer.interfaces.dto.KnowledgeBaseQueryReq;

/**
 * 知识库仓储接口
 *
 * @author dallas
 * @since 2025-10-24
 */
public interface KnowledgeBaseRepository extends IRepository<KnowledgeBase> {
    /**
     * 分页查询知识库
     *
     * @param page    分页信息
     * @param request 查询请求
     * @return 知识库分页结果
     */
    IPage<KnowledgeBase> page(IPage<KnowledgeBase> page, KnowledgeBaseQueryReq request);
}
