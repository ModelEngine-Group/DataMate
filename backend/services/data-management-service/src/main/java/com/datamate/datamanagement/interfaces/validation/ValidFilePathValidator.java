package com.datamate.datamanagement.interfaces.validation;

import com.datamate.datamanagement.infrastructure.exception.DataManagementErrorCode;
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;

import java.util.regex.Pattern;

/**
 * 文件路径校验器
 * 允许路径分隔符 / 用于支持文件夹上传
 *
 * @author DataMate
 * @since 2026/03/12
 */
public class ValidFilePathValidator implements ConstraintValidator<ValidFilePath, String> {

    /**
     * 文件路径正则表达式
     * 不允许包含特殊字符: \ : * ? " < > | \0
     * 允许字母、数字、中文、常见符号（- _ . space /）
     * 注意：允许 / 是为了支持文件夹上传的相对路径
     */
    private static final Pattern FILE_PATH_PATTERN = Pattern.compile(
        "^[^\\\\:*?\"<>|\\x00]+$"
    );

    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        if (value == null || value.isEmpty()) {
            return true; // 空值由 @NotBlank 等其他注解处理
        }

        boolean isValid = FILE_PATH_PATTERN.matcher(value).matches();

        if (!isValid) {
            context.disableDefaultConstraintViolation();
            context.buildConstraintViolationWithTemplate(
                DataManagementErrorCode.FILE_NAME_INVALID.getMessage()
            ).addConstraintViolation();
        }

        return isValid;
    }
}
