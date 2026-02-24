package com.datamate.datamanagement.interfaces.dto;

import com.datamate.datamanagement.interfaces.validation.ValidFileName;
import com.datamate.datamanagement.interfaces.validation.ValidPath;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

/**
 * 重命名数据集目录请求
 */
@Getter
@Setter
public class RenameDirectoryRequest {

    /** 目录前缀，例如 "images/"，与列表/删除目录接口保持一致 */
    @NotBlank(message = "目录前缀不能为空")
    @ValidPath(maxLength = 500)
    private String prefix;

    /** 新的目录名称 */
    @NotBlank(message = "新目录名称不能为空")
    @ValidFileName
    @Size(max = 255, message = "目录名称长度不能超过255个字符")
    private String newName;
}
