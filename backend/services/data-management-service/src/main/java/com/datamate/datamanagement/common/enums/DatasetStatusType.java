package com.datamate.datamanagement.common.enums;

/**
 * 数据集状态类型
 * <p>数据集可以处于以下几种状态：
 * <p>草稿（DRAFT）：数据集正在创建中，尚未完成。
 * <p>活动（ACTIVE）：数据集处于活动状态, 可以被查询和使用，也可以被更新和删除。
 * <p>处理中（PROCESSING）：数据集正在处理中，可能需要一些时间，处理完成后会变成活动状态。
 * <p>已归档（ARCHIVED）：数据集已被归档，不可以更新文件，可以解锁变成活动状态。
 * <p>已发布（PUBLISHED）：数据集已被发布，可供外部使用，外部用户可以查询和使用数据集。
 * <p>已弃用（DEPRECATED）：数据集已被弃用，不建议再使用。
 *
 * @author dallas
 * @since 2025-10-17
 */
public enum DatasetStatusType {
    /**
     * 草稿状态
     */
    DRAFT,
    /**
     * 活动状态
     */
    ACTIVE,
    /**
     * 处理中状态
     */
    PROCESSING,
    /**
     * 已归档状态
     */
    ARCHIVED,
    /**
     * 已发布状态
     */
    PUBLISHED,
    /**
     * 已弃用状态
     */
    DEPRECATED
}
