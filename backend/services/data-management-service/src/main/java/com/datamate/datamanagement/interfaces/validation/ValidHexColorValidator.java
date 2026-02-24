package com.datamate.datamanagement.interfaces.validation;

import com.datamate.datamanagement.infrastructure.exception.DataManagementErrorCode;
import com.datamate.common.infrastructure.exception.ErrorCode;
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;
import org.hibernate.validator.internal.constraintvalidators.bv.size.SizeValidatorForCharSequence;

import java.util.regex.Pattern;

/**
 * 十六进制颜色格式校验器
 *
 * @author DataMate
 * @since 2026/02/11
 */
public class ValidHexColorValidator implements ConstraintValidator<ValidHexColor, String> {

    /**
     * 十六进制颜色正则表达式
     * 支持 #RGB 和 #RRGGBB 格式
     */
    private static final Pattern HEX_COLOR_PATTERN = Pattern.compile("^#[0-9a-fA-F]{6}$");

    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        if (value == null) {
            return true; // null 值由 @NotBlank 等其他注解处理
        }

        boolean isValid = HEX_COLOR_PATTERN.matcher(value).matches();

        if (!isValid) {
            // 自定义错误消息和错误码
            context.disableDefaultConstraintViolation();
            context.buildConstraintViolationWithTemplate(
                DataManagementErrorCode.TAG_COLOR_INVALID.getMessage()
            ).addConstraintViolation();
        }

        return isValid;
    }
}
