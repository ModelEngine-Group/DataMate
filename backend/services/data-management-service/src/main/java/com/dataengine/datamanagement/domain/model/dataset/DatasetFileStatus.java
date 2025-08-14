package com.dataengine.datamanagement.domain.model.dataset;

/**
 * 数据集文件状态枚举
 */
public enum DatasetFileStatus {
    /**
     * 已上传
     */
    UPLOADED,
    
    /**
     * 处理中
     */
    PROCESSING,
    
    /**
     * 已完成
     */
    COMPLETED,
    
    /**
     * 错误
     */
    ERROR
}
