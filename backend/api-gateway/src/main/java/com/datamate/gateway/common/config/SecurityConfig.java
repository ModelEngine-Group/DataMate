package com.datamate.gateway.common.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.reactive.EnableWebFluxSecurity;
import org.springframework.security.config.web.server.ServerHttpSecurity;
import org.springframework.security.web.server.SecurityWebFilterChain;

/**
 * 安全配置 - 暂时禁用所有认证
 */
@Configuration
@EnableWebFluxSecurity
public class SecurityConfig {

    @Bean
    public SecurityWebFilterChain filterChain(ServerHttpSecurity http) throws Exception {
        http.csrf(ServerHttpSecurity.CsrfSpec::disable)
            .authorizeExchange(exchange ->
                    exchange.pathMatchers("**").permitAll()  // 允许所有请求无需认证
            );

        return http.build();
    }
}
