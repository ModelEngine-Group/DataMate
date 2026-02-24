package com.datamate.datamanagement.interfaces.dto;

import com.datamate.datamanagement.interfaces.validation.ValidFileName;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

/**
 * 重命名数据集文件请求
 */
@Getter
@Setter
public class RenameFileRequest {

    /** 新的文件名称（不包含后缀） */
    @NotBlank(message = "新文件名不能为空")
    @ValidFileName
    @Size(max = 255, message = "文件名称长度不能超过255个字符")
    private String newName;
}
