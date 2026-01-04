package com.datamate.datamanagement.interfaces.dto;

import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 数据集文件响应DTO
 */
@Getter
@Setter
public class DatasetFileResponse {
    /** 文件ID */
    private String id;
    /** 文件名 */
    private String fileName;
    /** 原始文件名 */
    private String originalName;
    /** 文件类型 */
    private String fileType;
    /** 文件大小（字节） */
    private Long fileSize;
    /** 文件状态 */
    private String status;
    /** 文件描述 */
    private String description;
    /** 文件路径 */
    private String filePath;
    /** 上传时间 */
    private LocalDateTime uploadTime;
    /** 最后更新时间 */
    private LocalDateTime lastAccessTime;
    /** 上传者 */
    private String uploadedBy;
    /** 是否为目录 */
    private Boolean directory;
    /** 目录文件数量 */
    private Long fileCount;
}
