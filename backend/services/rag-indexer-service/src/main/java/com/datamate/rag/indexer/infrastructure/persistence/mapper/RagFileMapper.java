package com.datamate.rag.indexer.infrastructure.persistence.mapper;


import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.common.infrastructure.config.IgnoreDataScopeAnnotation;
import com.datamate.rag.indexer.domain.model.RagFile;
import org.apache.ibatis.annotations.Mapper;

/**
 * RAG文件映射器接口
 *
 * @author dallas
 * @since 2025-10-24
 */
@Mapper
@IgnoreDataScopeAnnotation
public interface RagFileMapper extends BaseMapper<RagFile> {
}
