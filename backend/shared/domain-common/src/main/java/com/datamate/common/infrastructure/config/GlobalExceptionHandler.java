package com.datamate.common.infrastructure.config;

import com.datamate.common.infrastructure.common.Response;
import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.stream.Collectors;

/**
 *
 *
 * @author dallas
 * @since 2025-10-17
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {
    /**
     * 处理自定义业务异常
     */
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<Response<?>> handleBusinessException(BusinessException e) {
        log.warn("BusinessException: code={}, message={}", e.getCode(), e.getMessage(), e);
        return ResponseEntity.internalServerError().body(Response.error(e.getErrorCodeEnum()));
    }

    /**
     * 处理参数校验和数据绑定异常
     */
    @ExceptionHandler(value = {MethodArgumentNotValidException.class, BindException.class})
    public ResponseEntity<Response<?>> handleMethodArgumentNotValidException(BindException e) {
        String message = e.getBindingResult().getFieldErrors().stream()
            .map(FieldError::getDefaultMessage)
            .collect(Collectors.joining(", "));
        log.warn("Parameter validation failed: {}", message);
        return ResponseEntity.badRequest().body(Response.error(SystemErrorCode.INVALID_PARAMETER, message));
    }

    /**
     * 处理系统兜底异常
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Response<?>> handleException(Exception e) {
        log.error("SystemException: ", e);
        return ResponseEntity.internalServerError().body(Response.error(SystemErrorCode.SYSTEM_BUSY));
    }
}
