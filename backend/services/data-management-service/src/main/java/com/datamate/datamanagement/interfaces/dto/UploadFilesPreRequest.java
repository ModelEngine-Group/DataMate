package com.datamate.datamanagement.interfaces.dto;

import com.datamate.datamanagement.interfaces.validation.ValidPath;
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
    @Min(value = 1, message = "总文件数量必须大于0")
    private int totalFileNum;

    /** 总文件大小 */
    @Min(value = 1, message = "总文件大小必须大于0")
    private long totalSize;

    /** 目标子目录前缀，例如 "images/"，为空表示数据集根目录 */
    @ValidPath(maxLength = 500)
    private String prefix;
}
