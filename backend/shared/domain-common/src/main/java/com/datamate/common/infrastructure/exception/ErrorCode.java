package com.datamate.common.infrastructure.exception;

/**
 * 错误码接口
 *
 * @author dallas
 * @since 2025-10-17
 */
public interface ErrorCode {
    /**
     * 获取错误码
     *
     * @return 错误码
     */
    String getCode();

    /**
     * 获取错误信息
     *
     * @return 错误信息
     */
    String getMessage();
}
