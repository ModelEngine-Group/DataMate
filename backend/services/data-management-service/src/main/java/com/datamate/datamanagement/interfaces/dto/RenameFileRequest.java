package com.datamate.datamanagement.interfaces.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

/**
 * 重命名数据集文件请求
 */
@Getter
@Setter
public class RenameFileRequest {

    /** 新的文件名称（不包含后缀） */
    @NotBlank
    private String newName;
}
