package com.datamate.datamanagement.interfaces.validation;

import jakarta.validation.Constraint;
import jakarta.validation.Payload;

import java.lang.annotation.*;

/**
 * 文件名校验注解
 * 验证文件名不包含非法字符
 *
 * @author DataMate
 * @since 2026/02/11
 */
@Documented
@Constraint(validatedBy = ValidFileNameValidator.class)
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
public @interface ValidFileName {

    String message() default "文件名包含非法字符";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};
}
