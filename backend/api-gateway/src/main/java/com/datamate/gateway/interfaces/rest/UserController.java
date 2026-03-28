package com.datamate.gateway.interfaces.rest;

import com.datamate.common.infrastructure.common.IgnoreResponseWrap;
import com.datamate.common.infrastructure.common.Response;
import com.datamate.common.infrastructure.exception.CommonErrorCode;
import com.datamate.gateway.application.UserApplicationService;
import com.datamate.gateway.domain.service.UserService;
import com.datamate.gateway.interfaces.dto.LoginRequest;
import com.datamate.gateway.interfaces.dto.LoginResponse;
import com.datamate.gateway.interfaces.dto.RegisterRequest;
import com.datamate.gateway.interfaces.dto.UserResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

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
     * 1. SSO 模式：检查 OMS 请求头 (X-User-Name, X-User-Group-Id)
     * 2. JWT 模式：检查 Authorization Bearer Token
     * 3. 未登录：返回 authenticated=false
     *
     * @param request HTTP 请求
     * @return 用户信息（包含认证模式）
     */
    @GetMapping("/me")
    public Response<UserResponse> getCurrentUser(ServerHttpRequest request) {
        // 优先检查 SSO 模式（OMS 请求头）
        String ssoUsername = request.getHeaders().getFirst("X-User-Name");
        String ssoGroupId = request.getHeaders().getFirst("X-User-Group-Id");

        if (StringUtils.isNotBlank(ssoUsername)) {
            log.info("SSO mode: user={}, groupId={}", ssoUsername, ssoGroupId);
            return Response.ok(UserResponse.builder()
                    .username(ssoUsername)
                    .groupId(ssoGroupId)
                    .authenticated(true)
                    .authMode("SSO")
                    .build());
        }

        // 检查独立登录模式（JWT Token）
        String authHeader = request.getHeaders().getFirst("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            String username = userService.validateToken(token);

            if (StringUtils.isNotBlank(username)) {
                log.info("JWT mode: user={}", username);
                return Response.ok(UserResponse.builder()
                        .username(username)
                        .authenticated(true)
                        .authMode("JWT")
                        .build());
            }
        }

        // 未登录
        log.debug("User not authenticated");
        return Response.ok(UserResponse.builder()
                .authenticated(false)
                .authMode("NONE")
                .build());
    }
}
