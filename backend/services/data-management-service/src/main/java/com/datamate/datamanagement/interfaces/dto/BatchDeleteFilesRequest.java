package com.datamate.datamanagement.interfaces.dto;

import jakarta.validation.constraints.NotEmpty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 批量删除文件请求
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class BatchDeleteFilesRequest {

    /**
     * 要删除的文件ID列表
     */
    @NotEmpty(message = "文件ID列表不能为空")
    private List<String> fileIds;

    /**
     * 文件路径前缀（用于处理子目录中的文件）
     */
    private String prefix = "";
}
