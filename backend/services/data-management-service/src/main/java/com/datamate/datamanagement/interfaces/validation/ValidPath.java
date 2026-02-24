package com.datamate.datamanagement.interfaces.validation;

import jakarta.validation.Constraint;
import jakarta.validation.Payload;

import java.lang.annotation.*;

/**
 * 路径格式校验注解
 * 验证路径格式和长度限制
 *
 * @author DataMate
 * @since 2026/02/11
 */
@Documented
@Constraint(validatedBy = ValidPathValidator.class)
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
public @interface  ValidPath {

    String message() default "路径格式不正确";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};

    /**
     * 最大路径长度，默认500
     */
    int maxLength() default 500;
}
