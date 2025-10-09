package com.dataengine.datamanagement.interfaces.dto;

import lombok.Getter;
import lombok.Setter;
import java.util.Map;

/**
 * 数据集统计信息响应DTO
 */
@Getter
@Setter
public class DatasetStatisticsResponse {
    /** 总文件数 */
    private Integer totalFiles;
    /** 已完成文件数 */
    private Integer completedFiles;
    /** 总大小（字节） */
    private Long totalSize;
    /** 完成率（0-100） */
    private Float completionRate;
    /** 文件类型分布 */
    private Map<String, Integer> fileTypeDistribution;
    /** 状态分布 */
    private Map<String, Integer> statusDistribution;
}
