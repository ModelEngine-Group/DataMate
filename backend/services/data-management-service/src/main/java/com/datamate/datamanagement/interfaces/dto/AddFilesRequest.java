package com.datamate.datamanagement.interfaces.dto;

import com.datamate.datamanagement.interfaces.validation.ValidPath;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.apache.commons.collections4.CollectionUtils;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * AddFilesRequest
 *
 * @since 2026/2/9
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class AddFilesRequest {
    private boolean softAdd;

    @ValidPath
    private String prefix = "";

    @NotEmpty(message = "文件列表不能为空")
    @Size(max = 1000, message = "文件数量不能超过1000个")
    @Valid
    private List<FileRequest> files;

    public AddFilesRequest(List<String> paths) {
        if (CollectionUtils.isEmpty(paths)) {
            return;
        }
        this.files = paths.stream().map(path -> {
            FileRequest file = new FileRequest();
            file.setFilePath(path);
            return file;
        }).toList();
    }

    /**
     * 获取文件的前缀，优先使用文件自身的 prefix，为空时回退到请求级别的 prefix
     */
    public String getEffectivePrefix(FileRequest file) {
        return (file.getPrefix() != null && !file.getPrefix().isEmpty()) ? file.getPrefix() : prefix;
    }

    @Getter
    @Setter
    public static class FileRequest {
        @NotBlank(message = "文件路径不能为空")
        @Size(max = 1000, message = "文件路径长度不能超过1000个字符")
        private String filePath;

        @ValidPath
        private String prefix = "";

        private Map<String, Object> metadata = new HashMap<>();
    }
}
