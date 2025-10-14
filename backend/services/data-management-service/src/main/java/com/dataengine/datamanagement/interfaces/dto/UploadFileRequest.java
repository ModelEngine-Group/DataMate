package com.dataengine.datamanagement.interfaces.dto;

import lombok.Getter;
import lombok.Setter;
import org.springframework.web.multipart.MultipartFile;

/**
 * 上传文件请求
 * 用于分块上传文件时的请求参数封装，支持大文件分片上传功能
 */
@Getter
@Setter
public class UploadFileRequest {
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

    /** 文件分块的校验和（十六进制字符串），用于验证文件完整性 */
    private String checkSumHex;
}
