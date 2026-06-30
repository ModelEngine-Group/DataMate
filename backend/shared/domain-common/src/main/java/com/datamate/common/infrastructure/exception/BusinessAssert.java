package com.datamate.common.infrastructure.exception;

import java.util.Collection;

/**
 * 断言工具类，用于在业务逻辑中快速检查条件是否满足，不满足时抛出业务异常
 *
 * @author dallas
 * @since 2025-10-17
 */
public class BusinessAssert {
    public static void isTrue(boolean condition, ErrorCode errorCode) {
        if (!condition) {
            throw BusinessException.of(errorCode);
        }
    }

    public static void notNull(Object obj, ErrorCode errorCode) {
        if (obj == null) {
            throw BusinessException.of(errorCode);
        }
    }

    public static void notEmpty(Collection<?> collection, ErrorCode errorCode) {
        if (collection == null || collection.isEmpty()) {
            throw BusinessException.of(errorCode);
        }
    }

    public static void isTrue(boolean condition, ErrorCode errorCode, String customMessage) {
        if (!condition) {
            throw BusinessException.of(errorCode, customMessage);
        }
    }
}
