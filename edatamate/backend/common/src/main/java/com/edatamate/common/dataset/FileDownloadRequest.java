package com.edatamate.common.dataset;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

/**
 * The FileDownloadRequest
 *
 * @since 2025-07-21
 */
@Getter
@Setter
@AllArgsConstructor
public class FileDownloadRequest {
    private long datasetId;

    private List<Long> fileIds;

    private boolean isFull;
}
