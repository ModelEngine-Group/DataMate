package com.datamate.rag.indexer.domain.model;


import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import com.datamate.common.domain.model.base.BaseEntity;
import lombok.Getter;
import lombok.Setter;

import java.util.Map;

/**
 * Rag 文件实体类
 *
 * @author dallas
 * @since 2025-10-24
 */
@Getter
@Setter
@TableName("t_rag_file")
public class RagFile extends BaseEntity<String> {
    /**
     * 知识库ID
     */
    private String knowledgeBaseId;
    /**
     * 文件名
     */
    private String fileName;
    /**
     * 文件ID
     */
    private String fileId;
    /**
     * 分块数量
     */
    private Integer chunkCount;

    /**
     * 元数据
     */
    @TableField(typeHandler = JacksonTypeHandler.class)
    private Map<String, Object> metadata;

    private FileStatus status;
}
