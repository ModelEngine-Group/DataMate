package com.datamate.gateway.filter;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

/**
 * 用户信息过滤器
 *
 */
@Slf4j
@Component
public class UserContextFilter implements GlobalFilter {
    @Value("${commercial.switch:false}")
    private boolean isCommercial;

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        if (!isCommercial) {
            return chain.filter(exchange);
        }
        try {

        } catch (Exception e) {
            log.error("get current user info error", e);
            return chain.filter(exchange);
        }
        return chain.filter(exchange);
    }
}
