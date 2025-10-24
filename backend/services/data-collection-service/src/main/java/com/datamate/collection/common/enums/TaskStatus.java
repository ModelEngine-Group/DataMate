package com.datamate.collection.common.enums;

/**
 * 统一的任务和执行状态枚举
 * 任务和执行状态枚举: - DRAFT: 草稿状态 - READY: 就绪状态 - RUNNING: 运行中 - SUCCESS: 执行成功 (对应原来的COMPLETED/SUCCESS) - FAILED: 执行失败 - STOPPED: 已停止
 *
 * @author Data Mate Platform Team
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
