package com.datamate.common.infrastructure.config;

import com.datamate.common.infrastructure.common.IgnoreResponseWrap;
import com.datamate.common.infrastructure.common.Response;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.MethodParameter;
import org.springframework.http.MediaType;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.lang.Nullable;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.mvc.method.annotation.ResponseBodyAdvice;

/**
 * 全局响应处理器
 *
 * @author dallas
 * @since 2025-10-17
 */
@Slf4j
@RequiredArgsConstructor
@RestControllerAdvice(basePackages = "com.datamate")
public class GlobalResponseHandler implements ResponseBodyAdvice<Object> {
    private final ObjectMapper objectMapper;

    /**
     * 判断哪些返回值需要被包装。
     * 返回true表示执行beforeBodyWrite方法。
     */
    @Override
    public boolean supports(MethodParameter returnType, @Nullable Class converterType) {
        // 1. 如果返回类型已经是Response，直接跳过包装
        if (returnType.getParameterType().isAssignableFrom(Response.class)) {
            return false;
        }
        // 2. 检查方法或所在类上是否有@IgnoreResponseWrap的注解，如果有，返回false
        if (returnType.hasMethodAnnotation(IgnoreResponseWrap.class) ||
            returnType.getContainingClass().isAnnotationPresent(IgnoreResponseWrap.class)) {
            return false;
        }
        // 3. 默认情况下，对其他返回类型进行包装
        return true;
    }

    /**
     * 对响应体进行实际包装处理。
     */
    @Override
    public Object beforeBodyWrite(Object body,
                                  @Nullable MethodParameter returnType,
                                  @Nullable MediaType selectedContentType,
                                  @Nullable Class selectedConverterType,
                                  @Nullable ServerHttpRequest request,
                                  @Nullable ServerHttpResponse response) {
        // 如果返回体本身就是Response类型（通常来自异常处理），直接返回
        if (body instanceof Response) {
            return body;
        }

        // 如果返回值是String类型，需要特殊处理
        if (body instanceof String) {
            // 手动将Response对象序列化为JSON字符串返回
            try {
                return objectMapper.writeValueAsString(Response.ok(body));
            } catch (JsonProcessingException e) {
                // 记录日志或抛出运行时异常
                log.error("Error serializing response", e);
                throw new RuntimeException("Error converting response to JSON", e);
            }
        }
        // 对于正常的返回结果，统一包装成成功的Response
        return Response.ok(body);
    }
}
