package com.datamate.datamanagement.interfaces.validation;

import jakarta.validation.Constraint;
import jakarta.validation.Payload;

import java.lang.annotation.*;

/**
 * 文件路径校验注解
 * 验证文件路径不包含非法字符（允许 / 用于支持文件夹上传）
 *
 * @author DataMate
 * @since 2026/03/12
 */
@Documented
@Constraint(validatedBy = ValidFilePathValidator.class)
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
public @interface ValidFilePath {

    String message() default "文件路径包含非法字符";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};
}
