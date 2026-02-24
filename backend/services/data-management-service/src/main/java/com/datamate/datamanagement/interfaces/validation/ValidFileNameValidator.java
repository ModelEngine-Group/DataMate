package com.datamate.datamanagement.interfaces.validation;

import com.datamate.datamanagement.infrastructure.exception.DataManagementErrorCode;
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;

import java.util.regex.Pattern;

/**
 * 文件名校验器
 *
 * @author DataMate
 * @since 2026/02/11
 */
public class ValidFileNameValidator implements ConstraintValidator<ValidFileName, String> {

    /**
     * 文件名正则表达式
     * 不允许包含特殊字符: / \ : * ? " < > | \0
     * 允许字母、数字、中文、常见符号（- _ . space）
     */
    private static final Pattern FILE_NAME_PATTERN = Pattern.compile(
        "^[^/\\\\:*?\"<>|\\x00]+$"
    );

    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        if (value == null || value.isEmpty()) {
            return true; // 空值由 @NotBlank 等其他注解处理
        }

        boolean isValid = FILE_NAME_PATTERN.matcher(value).matches();

        if (!isValid) {
            context.disableDefaultConstraintViolation();
            context.buildConstraintViolationWithTemplate(
                DataManagementErrorCode.FILE_NAME_INVALID.getMessage()
            ).addConstraintViolation();
        }

        return isValid;
    }
}
