package com.datamate.rag.indexer.infrastructure.event;

import com.datamate.rag.indexer.domain.model.KnowledgeBase;
import com.datamate.rag.indexer.interfaces.dto.AddFilesReq;

/**
 * 数据插入事件
 *
 * @author dallas
 * @since 2025-10-29
 */
public record DataInsertedEvent(KnowledgeBase knowledgeBase, AddFilesReq addFilesReq) {
}
