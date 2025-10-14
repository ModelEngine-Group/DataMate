package com.dataengine.datamanagement.infrastructure.client.dto;

import lombok.Data;
import java.util.List;

/**
 * 本地归集任务配置
 */
@Data
public class LocalCollectionConfig {
    /**
     * 归集类型
     */
    private String type;
    
    /**
     * 文件路径列表
     */
    private List<String> filePaths;
    
    /**
     * 其他配置项
     */
    private String sourceType;
    private String targetType;
}
