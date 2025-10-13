package com.dataengine.cleaning.domain.model;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;


@Getter
@Setter
@NoArgsConstructor
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
    private Long size;
    /** 文件状态 */
    private String status;
    /** 文件描述 */
    private String description;
    /** 文件路径 */
    private String filePath;
    /** 上传时间 */
    private LocalDateTime uploadedAt;
    /** 最后更新时间 */
    private LocalDateTime lastAccessTime;
    /** 上传者 */
    private String uploadedBy;
}
