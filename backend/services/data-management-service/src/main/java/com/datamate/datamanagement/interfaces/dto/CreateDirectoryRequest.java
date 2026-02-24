package com.datamate.datamanagement.interfaces.dto;

import com.datamate.datamanagement.interfaces.validation.ValidFileName;
import com.datamate.datamanagement.interfaces.validation.ValidPath;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

/**
 * 创建数据集子目录请求
 */
@Getter
@Setter
public class CreateDirectoryRequest {

    /** 父级前缀路径，例如 "images/"，为空表示数据集根目录 */
    @ValidPath()
    private String parentPrefix;

    /** 新建目录名称 */
    @NotBlank(message = "目录名称不能为空")
    @ValidFileName
    @Size(max = 255, message = "目录名称长度不能超过255个字符")
    private String directoryName;
}
