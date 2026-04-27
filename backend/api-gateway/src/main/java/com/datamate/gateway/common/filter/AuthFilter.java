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
 * 支持两种场景：
 * 1. 商业场景（SSO）：OmsAuthFilter 已添加 X-User-Name header，直接使用
 * 2. 独立场景（可选登录）：
 *    - DATAMATE_JWT_ENABLED=true：必须登录，验证 JWT token 并添加 User header
 *    - DATAMATE_JWT_ENABLED=false：允许匿名访问，不添加 User header
 *
 * 优先级：SSO > JWT
 * Order: 2 (低于 OmsAuthFilter 的 Order=1)
 *
 * 环境变量：
 * - OMS_AUTH_ENABLED：是否启用 OmsAuthFilter（商业场景）
 * - DATAMATE_JWT_ENABLE：独立场景下是否要求用户登录
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

        // 公开接口：直接放行
        if (path.equals("/api/user/login") || path.equals("/api/user/signup")) {
            return chain.filter(exchange);
        }

        // 内部接口：/api/user/me 内部会自行验证 SSO 或 JWT，直接放行
        if (path.equals("/api/user/me")) {
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

            // 独立场景：根据 DATAMATE_JWT_ENABLE 决定是否要求登录
            if (!jwtEnable) {
                log.debug("JWT authentication is not required, passing request without user header");
                return chain.filter(exchange);
            }

            // JWT 模式：必须登录，验证 Token
            String authHeader = request.getHeaders().getFirst(AUTH_HEADER);
            if (authHeader == null || !authHeader.startsWith(TOKEN_PREFIX)) {
                log.warn("JWT authentication is required but no valid Authorization header found");
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
