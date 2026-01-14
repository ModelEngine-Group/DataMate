package com.datamate.gateway.interfaces.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * Login Request DTO
 */
@Data
public class LoginRequest {
    @NotBlank(message = "Username cannot be empty")
    private String username;
    
    @NotBlank(message = "Password cannot be empty")
    private String password;
}
