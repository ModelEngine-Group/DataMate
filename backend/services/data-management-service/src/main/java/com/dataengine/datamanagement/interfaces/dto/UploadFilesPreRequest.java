package com.dataengine.datamanagement.interfaces.dto;

import jakarta.validation.constraints.Min;
import lombok.Getter;
import lombok.Setter;

/**
 * 切片上传预上传请求
 */
@Getter
@Setter
public class UploadFilesPreRequest {
    /** 是否为压缩包上传 */
    private boolean hasArchive;

    /** 总文件数量 */
    @Min(1)
    private int totalFileNum;

    /** 总文件大小 */
    private long totalSize;
}
