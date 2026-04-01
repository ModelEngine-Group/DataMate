package com.datamate.gateway.interfaces.rest;

import com.datamate.common.infrastructure.common.IgnoreResponseWrap;
import com.datamate.common.infrastructure.common.Response;
import com.datamate.common.infrastructure.exception.CommonErrorCode;
import com.datamate.gateway.application.UserApplicationService;
import com.datamate.gateway.domain.service.UserService;
import com.datamate.gateway.infrastructure.client.OmsExtensionService;
import com.datamate.gateway.infrastructure.client.OmsService;
import com.datamate.gateway.interfaces.dto.LoginRequest;
import com.datamate.gateway.interfaces.dto.LoginResponse;
import com.datamate.gateway.interfaces.dto.RegisterRequest;
import com.datamate.gateway.interfaces.dto.UserResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.util.MultiValueMap;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.http.HttpCookie;

/**
 * UserController
 *
 * @since 2026/1/14
 */
@Slf4j
@Validated
@RestController
@RequestMapping("/api/user")
@RequiredArgsConstructor
public class UserController {
    private final UserApplicationService userApplicationService;
    private final UserService userService;
    private final OmsService omsService;
    private final OmsExtensionService omsExtensionService;

    @Value("${datamate.jwt.enable:false}")
    private Boolean jwtEnable;

    private static final String AUTH_TOKEN_KEY = "__Host-X-Auth-Token";
    private static final String CSRF_TOKEN_KEY = "__Host-X-Csrf-Token";

    /**
     * 从 cookies 中获取 token 值
     */
    private String getToken(MultiValueMap<String, HttpCookie> cookies, String tokenKey) {
        if (cookies.containsKey(tokenKey)) {
            return cookies.getFirst(tokenKey).getValue();
        }
        return "";
    }

    /**
     * 获取真实 IP 地址
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

    @PostMapping("/login")
    @IgnoreResponseWrap
    public ResponseEntity<Response<LoginResponse>> login(@Valid @RequestBody LoginRequest loginRequest) {
        return userApplicationService.login(loginRequest)
                .map(response -> ResponseEntity.ok(Response.ok(response)))
                .orElseGet(() -> ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .body(Response.error(CommonErrorCode.UNAUTHORIZED)));
    }

    @PostMapping("/signup")
    @IgnoreResponseWrap
    public ResponseEntity<Response<LoginResponse>> register(@Valid @RequestBody RegisterRequest registerRequest) {
        return userApplicationService.register(registerRequest)
                .map(response -> ResponseEntity.ok(Response.ok(response)))
                .orElseGet(() -> ResponseEntity.status(HttpStatus.BAD_REQUEST)
                        .body(Response.error(CommonErrorCode.SIGNUP_ERROR)));
    }

    /**
     * 获取当前登录用户信息（支持双模式）
     * 优先级：
     * 1. SSO 模式：从 cookies 读取 OMS token 并调用 OMS 服务验证
     * 2. JWT 模式：检查 Authorization Bearer Token
     * 3. 未登录：返回 authenticated=false
     *
     * @param request HTTP 请求
     * @return 用户信息（包含认证模式）
     */
    @GetMapping("/me")
    public Response<UserResponse> getCurrentUser(ServerHttpRequest request) {
        log.debug("=== /api/user/me called ===");

        // 优先检查 SSO 模式（从 cookies 读取 OMS token）
        MultiValueMap<String, HttpCookie> cookies = request.getCookies();
        String authToken = getToken(cookies, AUTH_TOKEN_KEY);
        String csrfToken = getToken(cookies, CSRF_TOKEN_KEY);

        log.debug("Cookies present - __Host-X-Auth-Token: {}, __Host-X-Csrf-Token: {}",
                StringUtils.isNotBlank(authToken), StringUtils.isNotBlank(csrfToken));

        if (StringUtils.isNotBlank(authToken)) {
            try {
                // 获取真实 IP
                String realIp = getRealIp(request);
                log.debug("Calling OMS service with realIp: {}", realIp);

                // 调用 OMS 服务验证
                String username = omsService.getUserNameFromOms(authToken, csrfToken, realIp);
                if (StringUtils.isNotBlank(username)) {
                    log.info("SSO authentication successful: user={}", username);

                    // 获取用户组 ID（可能为 null）
                    String groupId = null;
                    try {
                        groupId = omsExtensionService.getUserGroupId(username);
                        log.debug("User groupId: {}", groupId);
                    } catch (Exception e) {
                        log.warn("Failed to get user group ID: {}", e.getMessage());
                    }

                    return Response.ok(UserResponse.builder()
                            .username(username)
                            .groupId(groupId)
                            .authenticated(true)
                            .authMode("SSO")
                            .requireLogin(true)  // SSO 模式始终要求登录
                            .build());
                } else {
                    log.warn("OMS service returned null username");
                }
            } catch (Exception e) {
                log.error("SSO authentication failed", e);
            }
        }

        // 检查独立登录模式（JWT Token）
        String authHeader = request.getHeaders().getFirst("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            String username = userService.validateToken(token);

            if (StringUtils.isNotBlank(username)) {
                log.info("JWT authentication successful: user={}", username);
                return Response.ok(UserResponse.builder()
                        .username(username)
                        .authenticated(true)
                        .authMode("JWT")
                        .requireLogin(true)  // 已登录
                        .build());
            } else {
                log.warn("JWT token validation failed");
            }
        }

        // 未登录：检查是否强制要求登录
        boolean requireLogin = Boolean.TRUE.equals(jwtEnable);
        log.debug("User not authenticated, requireLogin={}, jwtEnable={}", requireLogin, jwtEnable);

        return Response.ok(UserResponse.builder()
                .authenticated(false)
                .authMode("NONE")
                .requireLogin(requireLogin)  // 关键字段：告诉前端是否需要登录
                .build());
    }
}
