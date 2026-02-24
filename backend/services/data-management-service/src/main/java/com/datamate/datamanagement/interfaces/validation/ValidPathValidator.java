package com.datamate.datamanagement.interfaces.validation;

import com.datamate.datamanagement.infrastructure.exception.DataManagementErrorCode;
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;

import java.util.regex.Pattern;

/**
 * 路径格式校验器
 *
 * @author DataMate
 * @since 2026/02/11
 */
public class ValidPathValidator implements ConstraintValidator<ValidPath, String> {

    /**
     * 路径正则表达式
     * 不允许以点开头（隐藏文件/目录）
     * 不允许包含特殊字符如 \0, <, >, :, ", |, ?, *
     */
    private static final Pattern PATH_PATTERN = Pattern.compile(
        "^[^<>:\"|?*\\x00]+" // 不以点开头，不包含特殊字符
    );

    private int maxLength = 500;

    @Override
    public void initialize(ValidPath constraintAnnotation) {
        this.maxLength = constraintAnnotation.maxLength();
    }

    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        if (value == null || value.isEmpty()) {
            return true; // 空值由其他注解处理
        }

        // 检查长度
        if (value.length() > maxLength) {
            context.disableDefaultConstraintViolation();
            context.buildConstraintViolationWithTemplate(
                DataManagementErrorCode.PATH_TOO_LONG.getMessage()
            ).addConstraintViolation();
            return false;
        }

        // 检查是否以点开头
        if (value.startsWith(".")) {
            context.disableDefaultConstraintViolation();
            context.buildConstraintViolationWithTemplate(
                DataManagementErrorCode.PREFIX_INVALID.getMessage()
            ).addConstraintViolation();
            return false;
        }

        // 检查是否包含非法字符
        if (!PATH_PATTERN.matcher(value).matches()) {
            context.disableDefaultConstraintViolation();
            context.buildConstraintViolationWithTemplate("路径包含非法字符").addConstraintViolation();
            return false;
        }

        return true;
    }
}
