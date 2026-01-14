package com.datamate.gateway.application;

import com.datamate.gateway.domain.entity.User;
import com.datamate.gateway.domain.service.UserService;
import com.datamate.gateway.interfaces.dto.LoginRequest;
import com.datamate.gateway.interfaces.dto.LoginResponse;
import com.datamate.gateway.interfaces.dto.RegisterRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

/**
 * UserApplicationServices
 *
 * @since 2026/1/14
 */
@Slf4j
@Service
@Transactional
@RequiredArgsConstructor
public class UserApplicationService {
    private final UserService userService;

    public Optional<LoginResponse> login(LoginRequest loginRequest) {
        User user = new User();
        user.setUsername(loginRequest.getUsername());
        user.setPassword(loginRequest.getPassword());
        
        Optional<User> authenticatedUser = userService.authenticate(user);
        if (authenticatedUser.isPresent()) {
            User userEntity = authenticatedUser.get();
            return Optional.of(convertToLoginResponse(userEntity));
        }
        return Optional.empty();
    }

    /**
     * Register a new user
     *
     * @param registerRequest registration request
     * @return LoginResponse with user details and token if registration successful, empty otherwise
     */
    public Optional<LoginResponse> register(RegisterRequest registerRequest) {
        return userService.register(registerRequest)
                .map(this::convertToLoginResponse);
    }

    private LoginResponse convertToLoginResponse(User user) {
        return LoginResponse.builder()
                .id(user.getId())
                .username(user.getUsername())
                .email(user.getEmail())
                .token(user.getToken())
                .build();
    }
}
