package com.datamate.rag.indexer.interfaces.dto;

import com.datamate.common.interfaces.PagingQuery;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 *
 *
 * @author dallas
 * @since 2025-10-29
 */
@Setter
@Getter
public class KnowledgeBaseQueryReq extends PagingQuery {
    private String name;
    private String description;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private String createdBy;
    private String updatedBy;
}
