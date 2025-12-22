package com.datamate.gateway.filter;

import com.terrabase.enterprise.api.dto.LoginUserDto;
import com.terrabase.enterprise.api.sdk.TerrabaseSDK;
import com.terrabase.enterprise.api.sdk.TerrabaseSDKConfig;
import jakarta.annotation.PostConstruct;
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
 * @since 2025/12/22
 */
@Slf4j
@Component
public class UserContextFilter implements GlobalFilter {
    @Value("${terrabase.jar.path:/opt/terrabase}")
    private String jarPath;

    @Value("${commercial.switch:false}")
    private boolean isCommercial;

    private TerrabaseSDK terrabaseSDK;

    @PostConstruct
    public void init() {
        TerrabaseSDKConfig sdkConfig = TerrabaseSDKConfig.createDefault();
        sdkConfig.setJarPath(jarPath);
        terrabaseSDK = TerrabaseSDK.init(sdkConfig);
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        if (!isCommercial) {
            return chain.filter(exchange);
        }
        try {
            LoginUserDto loginUserDto = terrabaseSDK.userManagement().getCurrentUserInfo().getData().getFirst();
        } catch (Exception e) {
            log.error("get current user info error", e);
            return chain.filter(exchange);
        }
        return chain.filter(exchange);
    }
}
