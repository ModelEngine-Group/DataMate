package com.dataengine.common.domain.model;

import lombok.Getter;
import lombok.Setter;
import org.springframework.web.multipart.MultipartFile;

/**
 * 文件切片上传请求实体（与数据库表 t_chunk_upload_request 对齐）
 */
@Getter
@Setter
public class ChunkUploadRequest {
    /** 预上传返回的id，用来确认同一个任务 */
    private String reqId;

    /** 文件编号，用于标识批量上传中的第几个文件 */
    private int fileNo;

    /** 文件名称 */
    private String fileName;

    /** 文件总分块数量 */
    private int totalChunkNum;

    /** 当前分块编号，从1开始 */
    private int chunkNo;

    /** 上传的文件分块内容 */
    private MultipartFile file;

    /** 切片大小 */
    private Long fileSize;

    /** 文件分块的校验和（十六进制字符串），用于验证文件完整性 */
    private String checkSumHex;
}
