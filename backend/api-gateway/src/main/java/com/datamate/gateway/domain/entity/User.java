package com.datamate.gateway.domain.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 用户
 *
 * @since 2026/1/12
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@TableName(value = "users", autoResultMap = true)
public class User {
    private Long id;
    private String username;
    private String email;
    private String passwordHash;
    private String fullName;
    private String role;
    private boolean enabled;
    private LocalDateTime lastLoginAt;

    @TableField(exist = false)
    private String password;

    @TableField(exist = false)
    private String token;
}
