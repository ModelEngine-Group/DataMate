package com.datamate.common.infrastructure.config;

import java.lang.annotation.*;

/**
 * 忽略数据隔离注解
 * 该注解添加到对应的mapper上，添加后该mapper的方法查询时就不需要进行用户过滤了
 *
 * @since 2026/1/20
 */
@Documented
@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.TYPE, ElementType.METHOD})
public @interface IgnoreDataScopeAnnotation {
}
