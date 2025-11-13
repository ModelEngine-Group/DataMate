package com.datamate.datamanagement.interfaces.dto;

import jakarta.validation.constraints.NotEmpty;

import java.util.List;

/**
 * 复制文件请求DTO
 *
 * @author dallas
 * @since 2025-11-13
 */
public record CopyFilesRequest(@NotEmpty List<String> sourcePaths) {
}
