package com.datamate.gateway.interfaces.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 用户信息响应
 *
 * 支持双认证模式：
 * - SSO: 通过 OMS 单点登录
 * - JWT: 通过本地 JWT Token 认证
 * - NONE: 未登录
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserResponse {
    /**
     * 用户名
     */
    private String username;

    /**
     * 邮箱（JWT 模式可用）
     */
    private String email;

    /**
     * 用户组 ID（SSO 模式可用）
     */
    private String groupId;

    /**
     * 是否已认证
     */
    private Boolean authenticated;

    /**
     * 认证模式
     */
    private String authMode;  // "SSO" | "JWT" | "NONE"

    /**
     * 是否强制要求登录（由 datamate.jwt.enable 控制）
     */
    private Boolean requireLogin;
}
