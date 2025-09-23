package com.dataengine.collection.domain.model;

/**
 * 统一的任务和执行状态枚举
 * 
 * @author Data Engine Platform Team
 */
public enum TaskStatus {
    /** 草稿状态 */
    DRAFT,
    /** 就绪状态 */
    READY, 
    /** 运行中 */
    RUNNING, 
    /** 执行成功（对应原来的COMPLETED） */
    SUCCESS, 
    /** 执行失败 */
    FAILED, 
    /** 已停止 */
    STOPPED
}
