package com.datamate.datamanagement.interfaces.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

/**
 * 重命名数据集目录请求
 */
@Getter
@Setter
public class RenameDirectoryRequest {

    /** 目录前缀，例如 "images/"，与列表/删除目录接口保持一致 */
    @NotBlank
    private String prefix;

    /** 新的目录名称 */
    @NotBlank
    private String newName;
}
