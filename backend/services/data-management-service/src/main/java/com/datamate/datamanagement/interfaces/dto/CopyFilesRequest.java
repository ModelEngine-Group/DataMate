package com.datamate.datamanagement.interfaces.dto;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;

import java.util.List;

/**
 * 复制文件请求DTO
 *
 * @author dallas
 * @since 2025-11-13
 */
public record CopyFilesRequest(
    @NotEmpty(message = "源文件路径列表不能为空")
    @Size(max = 1000, message = "文件数量不能超过1000个")
    List<String> sourcePaths) {
}
