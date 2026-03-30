package com.datamate.gateway.common.filter;

import com.datamate.common.infrastructure.common.Response;
import com.datamate.common.infrastructure.exception.CommonErrorCode;
import com.datamate.gateway.domain.service.UserService;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.nio.charset.StandardCharsets;

/**
 * 用户数据隔离过滤器
 *
 * 支持两种认证模式：
 * 1. SSO 模式：从 OmsAuthFilter 添加的 X-User-Name header 中提取用户信息
 * 2. JWT 模式：从 Authorization Bearer Token 中提取用户信息
 *
 * 无论哪种模式，最终都会添加 User header 供下游服务隔离用户数据
 *
 * 优先级：SSO > JWT
 * Order: 2 (低于 OmsAuthFilter 的 Order=1)
 *
 * @author songyongtan
 * @date 2026-03-30
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AuthFilter implements GlobalFilter, Ordered {
    private static final String AUTH_HEADER = "Authorization";

    private static final String TOKEN_PREFIX = "Bearer ";

    private static final String USER_HEADER = "User";

    private final UserService userService;

    @Value("${datamate.jwt.enable:false}")
    private Boolean jwtEnable;

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getURI().getPath();
        if (path.equals("/api/user/login") || path.equals("/api/user/signup")) {
            return chain.filter(exchange);
        }

        try {
            // 优先检查 SSO 模式（OmsAuthFilter 已添加的 header）
            String ssoUser = request.getHeaders().getFirst("X-User-Name");
            if (StringUtils.isNotBlank(ssoUser)) {
                log.info("SSO mode detected, adding User header: {}", ssoUser);
                ServerHttpRequest mutatedRequest = request.mutate()
                        .headers(httpHeaders -> {
                            httpHeaders.add(USER_HEADER, ssoUser);
                        })
                        .build();
                ServerWebExchange mutatedExchange = exchange.mutate()
                        .request(mutatedRequest)
                        .build();
                return chain.filter(mutatedExchange);
            }

            // 检查 JWT 模式
            if (!jwtEnable) {
                log.debug("JWT is disabled, passing request without user header");
                return chain.filter(exchange);
            }

            // JWT 模式：验证 Token
            String authHeader = request.getHeaders().getFirst(AUTH_HEADER);
            if (authHeader == null || !authHeader.startsWith(TOKEN_PREFIX)) {
                log.warn("JWT enabled but no valid Authorization header found");
                return sendUnauthorizedResponse(exchange);
            }

            String token = authHeader.substring(TOKEN_PREFIX.length());
            String user = userService.validateToken(token);
            if (StringUtils.isBlank(user)) {
                log.warn("JWT token validation failed");
                return sendUnauthorizedResponse(exchange);
            }

            log.info("JWT mode authenticated, adding User header: {}", user);
            ServerHttpRequest mutatedRequest = request.mutate()
                    .headers(httpHeaders -> {
                        httpHeaders.add(USER_HEADER, user);
                    })
                    .build();
            ServerWebExchange mutatedExchange = exchange.mutate()
                    .request(mutatedRequest)
                    .build();
            return chain.filter(mutatedExchange);
        } catch (Exception e) {
            log.error("Error in AuthFilter", e);
            return sendUnauthorizedResponse(exchange);
        }
    }

    private Mono<Void> sendUnauthorizedResponse(ServerWebExchange exchange) {
        ServerHttpResponse response = exchange.getResponse();
        response.setStatusCode(HttpStatus.UNAUTHORIZED);
        response.getHeaders().setContentType(MediaType.APPLICATION_JSON);
        ObjectMapper objectMapper = new ObjectMapper();
        byte[] bytes;
        try {
            bytes = objectMapper.writeValueAsString(Response.error(CommonErrorCode.UNAUTHORIZED)).getBytes(StandardCharsets.UTF_8);
        } catch (JsonProcessingException e) {
            String responseBody = "{\"code\":401,\"message\":\"登录失败：用户名或密码错误\",\"data\":null}";
            bytes = responseBody.getBytes(StandardCharsets.UTF_8);
        }
        DataBuffer buffer = response.bufferFactory().wrap(bytes);
        return response.writeWith(Mono.just(buffer));
    }

    /**
     * 用户数据隔离过滤器优先级
     *
     * Order = 2，在 OmsAuthFilter (Order=1) 之后执行
     * 确保先执行 SSO 认证，再执行用户数据隔离
     *
     * @return order value (2 = after SSO authentication)
     */
    @Override
    public int getOrder() {
        return 2;
    }
}
