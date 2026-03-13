package com.datamate.datamanagement.interfaces.dto;

import com.datamate.datamanagement.interfaces.validation.ValidFilePath;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
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
    @NotBlank(message = "请求ID不能为空")
    private String reqId;

    /** 文件编号，用于标识批量上传中的第几个文件 */
    @Min(value = 0, message = "文件编号必须为非负整数")
    private int fileNo;

    /** 文件名称（支持相对路径，用于文件夹上传） */
    @NotBlank(message = "文件名称不能为空")
    @ValidFilePath
    @Size(max = 255, message = "文件名称长度不能超过255个字符")
    private String fileName;

    /** 文件总分块数量 */
    @Min(value = 1, message = "总分块数量必须大于0")
    private int totalChunkNum;

    /** 当前分块编号，从1开始 */
    @Min(value = 1, message = "分块编号必须大于0")
    private int chunkNo;

    /** 上传的文件分块内容 */
    @NotNull(message = "文件内容不能为空")
    private MultipartFile file;

    /** 文件分块的校验和（十六进制字符串），用于验证文件完整性 */
    @Pattern(regexp = "^[0-9a-fA-F]{64}$", message = "校验和格式不正确，应为64位十六进制字符串")
    private String checkSumHex;
}
