package com.datamate.rag.indexer.interfaces.dto;

import com.datamate.common.interfaces.PagingQuery;
import lombok.Getter;
import lombok.Setter;

/**
 * RAG 文件请求
 *
 * @author dallas
 * @since 2025-10-29
 */
@Setter
@Getter
public class RagFileReq extends PagingQuery {
    private String fileName;
    private String knowledgeBaseId;
}
