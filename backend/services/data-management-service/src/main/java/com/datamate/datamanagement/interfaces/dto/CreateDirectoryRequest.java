package com.datamate.datamanagement.interfaces.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

/**
 * 创建数据集子目录请求
 */
@Getter
@Setter
public class CreateDirectoryRequest {

    /** 父级前缀路径，例如 "images/"，为空表示数据集根目录 */
    private String parentPrefix;

    /** 新建目录名称 */
    @NotBlank
    private String directoryName;
}
