package com.dataengine.common.domain.model;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 文件切片上传请求实体（与数据库表 t_chunk_upload_request 对齐）
 */
@Getter
@Setter
@Builder
public class ChunkUploadPreRequest {

    private String id; // UUID
    private Integer totalFileNum; // 总文件数
    private Integer uploadedFileNum; // 已上传文件数
    private String uploadPath; // 文件路径
    private LocalDateTime timeout; // 上传请求超时时间
    private String serviceId; // 上传请求所属服务：DATA-MANAGEMENT(数据管理)
    private String checkInfo; // 业务信息

    /**
     * 增加已上传文件数
     */
    public void incrementUploadedFileNum() {
        if (this.uploadedFileNum == null) {
            this.uploadedFileNum = 1;
        }
        this.uploadedFileNum++;
    }

    /**
     * 检查是否已完成上传
     */
    public boolean isUploadComplete() {
        return this.uploadedFileNum != null && this.uploadedFileNum.equals(this.totalFileNum);
    }

    /**
     * 检查是否已超时
     */
    public boolean isRequestTimeout() {
        return this.timeout != null && LocalDateTime.now().isAfter(this.timeout);
    }
}
