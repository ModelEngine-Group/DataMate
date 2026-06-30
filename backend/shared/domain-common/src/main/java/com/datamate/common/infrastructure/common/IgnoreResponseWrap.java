package com.datamate.common.infrastructure.common;

import java.lang.annotation.*;

/**
 * 忽略响应包装注解
 * <p>
 * 在使用全局响应包装时，如果某个接口或类不需要进行响应包装，可以使用此注解进行标记
 * </p>
 */
@Target({ElementType.METHOD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface IgnoreResponseWrap {
}
