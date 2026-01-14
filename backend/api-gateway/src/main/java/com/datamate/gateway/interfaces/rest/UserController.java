package com.datamate.gateway.interfaces.rest;

import com.datamate.common.infrastructure.common.IgnoreResponseWrap;
import com.datamate.common.infrastructure.common.Response;
import com.datamate.common.infrastructure.exception.CommonErrorCode;
import com.datamate.gateway.application.UserApplicationService;
import com.datamate.gateway.interfaces.dto.LoginRequest;
import com.datamate.gateway.interfaces.dto.LoginResponse;
import com.datamate.gateway.interfaces.dto.RegisterRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
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
}
