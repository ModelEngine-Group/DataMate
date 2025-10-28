package com.datamate.datamanagement.interfaces.dto;

import lombok.Getter;
import lombok.Setter;

/**
 * 所有数据集统计信息响应DTO
 */
@Getter
@Setter
public class AllDatasetStatisticsResponse {
    /** 总数据集数 */
    private Integer totalDatasets = 0;

    /** 总文件数 */
    private Long totalSize = 0L;

    /** 总大小（字节） */
    private Long totalFiles = 0L;
}
