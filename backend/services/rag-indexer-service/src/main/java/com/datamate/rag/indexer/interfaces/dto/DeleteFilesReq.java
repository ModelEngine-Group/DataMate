package com.datamate.rag.indexer.interfaces.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

/**
 * 删除文件请求
 *
 * @author dallas
 * @since 2025-10-29
 */
@Setter
@Getter
public class DeleteFilesReq {
    /**
     * Rag文件表主键ID列表
     */
    private List<String> ids;
}
