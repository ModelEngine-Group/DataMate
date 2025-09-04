package com.dataengine.datamanagement.domain.model.dataset;

/**
 * 状态常量类 - 统一管理所有状态枚举值
 */
public final class StatusConstants {
    
    /**
     * 数据集状态
     */
    public static final class DatasetStatuses {
        public static final String DRAFT = "DRAFT";
        public static final String ACTIVE = "ACTIVE";
        public static final String ARCHIVED = "ARCHIVED";
        public static final String PROCESSING = "PROCESSING";
        
        private DatasetStatuses() {}
    }
    
    /**
     * 数据集文件状态
     */
    public static final class DatasetFileStatuses {
        public static final String UPLOADED = "UPLOADED";
        public static final String PROCESSING = "PROCESSING";
        public static final String COMPLETED = "COMPLETED";
        public static final String ERROR = "ERROR";
        
        private DatasetFileStatuses() {}
    }
    
    private StatusConstants() {}
}
