package com.datamate.gateway.common.filter;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpCookie;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.util.MultiValueMap;
import org.springframework.web.server.ServerWebExchange;

import com.datamate.gateway.infrastructure.client.OmsExtensionService;
import com.datamate.gateway.infrastructure.client.OmsService;

import reactor.core.publisher.Mono;

import java.util.Objects;

/**
 * OmsAuthFilter is a global filter that authenticates requests to the OMS service.
 *
 * @author songyongtan
 * @date 2026-03-16
 */
@Slf4j
@Component
public class OmsAuthFilter implements GlobalFilter, Ordered {
    private static final String USER_NAME_HEADER = "X-User-Name";
    private static final String USER_GROUP_ID_HEADER = "X-User-Group-Id";
    private static final String AUTH_TOKEN_KEY = "__Host-X-Auth-Token";
    private static final String CSRF_TOKEN_KEY = "__Host-X-Csrf-Token";

    private final Boolean omsAuthEnable;
    private final OmsService omsService;
    private final OmsExtensionService omsExtensionService;

    /**
     * OmsAuthFilter constructor.
     * 
     * @param omsAuthEnable       whether OMS authentication is enabled
     * @param omsService          OMS service client
     * @param omsExtensionService OMS extension service client
     */
    public OmsAuthFilter(
            @Value("${oms.auth.enabled:false}") Boolean omsAuthEnable,
            OmsService omsService,
            OmsExtensionService omsExtensionService) {
        log.info("OmsAuthFilter is apply, omsAuthEnable: {}", omsAuthEnable);
        this.omsAuthEnable = omsAuthEnable;
        this.omsService = omsService;
        this.omsExtensionService = omsExtensionService;
    }

    /**
     * filter processes the request and adds authentication headers.
     * 
     * @param exchange the server web exchange
     * @param chain    the gateway filter chain
     * @return Mono<Void> completion signal
     */
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        if (!this.omsAuthEnable) {
            return chain.filter(exchange);
        }
        ServerHttpRequest request = exchange.getRequest();
        String uri = request.getURI().getPath();
        log.info("Oms auth filter uri: {}", uri);

        try {
            MultiValueMap<String, HttpCookie> cookies = request.getCookies();
            String authToken = getToken(cookies, AUTH_TOKEN_KEY);
            String csrfToken = getToken(cookies, CSRF_TOKEN_KEY);
            String realIp = getRealIp(request);

            String userName = this.omsService.getUserNameFromOms(authToken, csrfToken, realIp);
            if (userName == null) {
                exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
                log.error("Authentication failed: Token is null or invalid.");
                return exchange.getResponse().setComplete();
            }
            log.info("Current oms username is: {}", userName);
            ServerHttpRequest newRequest = request.mutate()
                    .header(USER_NAME_HEADER, userName)
                    .build();

            return chain.filter(exchange.mutate().request(newRequest).build());
        } catch (Exception e) {
            log.error("Exception occurred during POST request: {}", e.getMessage(), e);
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }
    }

    /**
     * getRealIp gets the real IP address from the request.
     * 
     * @param request the HTTP request
     * @return the real IP address
     */
    private String getRealIp(ServerHttpRequest request) {
        String ip = request.getHeaders().getFirst("X-Real-IP");
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeaders().getFirst("X-Forwarded-For");
        }
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeaders().getFirst("Proxy-Client-IP");
        }
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeaders().getFirst("WL-Proxy-Client-IP");
        }
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getRemoteAddress() != null ? request.getRemoteAddress().getAddress().getHostAddress() : "";
        }
        if (ip != null && ip.contains(",")) {
            ip = ip.split(",")[0].trim();
        }
        return ip != null ? ip : "";
    }

    /**
     * getToken gets the token value from cookies.
     *
     * @param cookies  the cookies map
     * @param tokenKey the token key
     * @return the token value
     */
    private String getToken(MultiValueMap<String, HttpCookie> cookies, String tokenKey) {
        if (cookies.containsKey(tokenKey)) {
            return Objects.requireNonNull(cookies.getFirst(tokenKey)).getValue();
        }
        return "";
    }

    /**
     * SSO 认证优先级最高
     *
     * @return order value (1 = highest priority for auth filters)
     */
    @Override
    public int getOrder() {
        return 1;
    }
}
