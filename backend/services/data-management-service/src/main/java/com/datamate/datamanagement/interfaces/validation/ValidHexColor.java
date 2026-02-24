package com.datamate.datamanagement.interfaces.validation;

import jakarta.validation.Constraint;
import jakarta.validation.Payload;

import java.lang.annotation.*;

/**
 * 十六进制颜色格式校验注解
 * 验证字符串是否符合十六进制颜色格式 (#RRGGBB 或 #RGB)
 *
 * @author DataMate
 * @since 2026/02/11
 */
@Documented
@Constraint(validatedBy = ValidHexColorValidator.class)
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
public @interface ValidHexColor {

    String message() default "标签颜色格式不正确，应为十六进制颜色代码";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};
}
