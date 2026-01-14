package com.datamate.gateway.interfaces.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

/**
 * Register Request DTO
 */
@Data
public class RegisterRequest {
    @NotBlank(message = "Username cannot be empty")
    @Size(min = 3, max = 50, message = "Username must be between 3 and 50 characters")
    private String username;

    @NotBlank(message = "Email cannot be empty")
    @Email(message = "Email should be valid")
    private String email;

    @NotBlank(message = "Password cannot be empty")
    @Size(min = 6, max = 100, message = "Password must be between 6 and 100 characters")
    private String password;
}
