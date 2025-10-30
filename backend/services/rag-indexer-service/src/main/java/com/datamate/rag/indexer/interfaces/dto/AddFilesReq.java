package com.datamate.rag.indexer.interfaces.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

/**
 * 添加文件请求
 *
 * @author dallas
 * @since 2025-10-29
 */
@Getter
@Setter
public class AddFilesReq {
    private String knowledgeBaseId;
    private ProcessType processType;
    private List<FileInfo> files;

    public record FileInfo(String fileId, String fileName) {
    }
}
