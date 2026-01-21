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
 * 鉴权过滤器
 *
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AuthFilter implements GlobalFilter {
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
            if (!jwtEnable) {
                return chain.filter(exchange);
            }
            // Get token from Authorization header
            String authHeader = request.getHeaders().getFirst(AUTH_HEADER);
            if (authHeader == null || !authHeader.startsWith(TOKEN_PREFIX)) {
                return sendUnauthorizedResponse(exchange);
            }
            String token = authHeader.substring(TOKEN_PREFIX.length());
            String user = userService.validateToken(token);
            if (StringUtils.isBlank(user)) {
                return sendUnauthorizedResponse(exchange);
            }
            // 4. 创建新的请求
            ServerHttpRequest mutatedRequest = request.mutate()
                    .headers(httpHeaders -> {
                        // 或者直接操作headers
                        httpHeaders.add(USER_HEADER, user);
                    })
                    .build();
            // 5. 使用新的请求创建新的exchange
            ServerWebExchange mutatedExchange = exchange.mutate()
                    .request(mutatedRequest)
                    .build();
            return chain.filter(mutatedExchange);
        } catch (Exception e) {
            log.error("get current user info error", e);
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
}
