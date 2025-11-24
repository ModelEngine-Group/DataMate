package com.datamate.rag.indexer.interfaces.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

/**
 * 检索请求
 *
 * @author dallas
 * @since 2025-11-20
 */
@Getter
@Setter
public class RetrieveReq {
    private String query;
    private int topK;
    private Float threshold;
    private List<String> knowledgeBaseIds;
}
