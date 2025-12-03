package com.datamate.datamanagement.interfaces.dto;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;

import java.util.List;

/**
 * 添加文件请求DTO（仅创建DB记录，不执行文件系统操作）
 *
 * @author datamate
 * @since 2025-11-29
 */
public record AddFilesRequest(
        @NotEmpty List<String> sourcePaths,
        @NotNull Boolean softAdd
) {
}
