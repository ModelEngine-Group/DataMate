package com.datamate.rag.indexer.infrastructure.persistence.mapper;


import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.rag.indexer.domain.model.KnowledgeBase;
import org.apache.ibatis.annotations.Mapper;

/**
 * 知识库映射器接口
 *
 * @author dallas
 * @since 2025-10-24
 */
@Mapper
public interface KnowledgeBaseMapper extends BaseMapper<KnowledgeBase> {
}
