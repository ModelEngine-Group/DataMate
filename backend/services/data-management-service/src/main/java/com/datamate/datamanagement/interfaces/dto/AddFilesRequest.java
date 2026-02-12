package com.datamate.datamanagement.interfaces.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.commons.lang3.StringUtils;

import java.util.List;
import java.util.Map;

/**
 * AddFilesRequest1
 *
 * @since 2026/2/9
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class AddFilesRequest {
    public AddFilesRequest(List<String> paths) {
        if (CollectionUtils.isEmpty(paths)) {
            return;
        }
        this.files = paths.stream().map(path -> {
            AddFilesRequest.FileRequest file = new AddFilesRequest.FileRequest();
            file.setFilePath(path);
            return  file;
        }).toList();
    }

    @Getter
    @Setter
    public static class FileRequest {
        private String filePath;

        private Map<String, Object> metadata;
    }

    private boolean softAdd;

    private String prefix = "";

    private List<FileRequest> files;

    public boolean isValidPrefix() {
        return StringUtils.isEmpty(prefix) || (!prefix.startsWith("."));
    }
}
