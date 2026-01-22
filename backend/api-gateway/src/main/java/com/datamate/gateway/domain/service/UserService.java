package com.datamate.gateway.domain.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.datamate.gateway.domain.entity.User;
import com.datamate.gateway.domain.repository.UserRepository;
import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.Optional;

import com.datamate.gateway.interfaces.dto.RegisterRequest;

/**
 * UserService
 *
 * @since 2026/1/12
 */
@Service
@RequiredArgsConstructor
public class UserService {
    private static final String SYSTEM_USER = "system";

    private final UserRepository userRepository;

    @Value("${datamate.jwt.expiration-seconds:3600}")
    private long expirationSeconds;

    @Value("${datamate.jwt.secret}")
    private String secret;

    /**
     * Authenticate user with username and password
     *
     * @param user user to authenticate
     * @return authenticated user with token if successful, empty otherwise
     */
    public Optional<User> authenticate(User user) {
        LambdaQueryWrapper<User> userWrapper = new LambdaQueryWrapper<>();
        userWrapper.eq(User::getUsername, user.getUsername());
        User userInDB = userRepository.getOne(userWrapper);
        
        if (userInDB != null && validPassword(user, userInDB)) {
            String token = generateToken(userInDB);
            userInDB.setToken(token);
            return Optional.of(userInDB);
        }
        return Optional.empty();
    }

    private boolean validPassword(User user, User userInDB) {
        BCryptPasswordEncoder encoder = new BCryptPasswordEncoder(10); // cost=10
        return encoder.matches(user.getPassword(), userInDB.getPasswordHash());
    }

    private String generateToken(User user) {
        long now = System.currentTimeMillis();
        return Jwts.builder()
                .setSubject(user.getUsername())
                .claim("uid", user.getId())
                .claim("role", user.getRole())
                .setIssuedAt(new Date(now))
                .setExpiration(new Date(now + expirationSeconds * 1000))
                .signWith(Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8)), SignatureAlgorithm.HS256)
                .compact();
    }

    public String validateToken(String token) {
        try {
            Jws<Claims> claimsJws = Jwts.parserBuilder().setSigningKey(Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8))).build().parseClaimsJws(token);
            return claimsJws.getBody().getSubject();
        } catch (JwtException | IllegalArgumentException ex) {
            return null;
        }
    }

    /**
     * Register a new user
     *
     * @param registerRequest registration request containing user details
     * @return registered user with token if successful, empty if username or email already exists
     */
    public Optional<User> register(RegisterRequest registerRequest) {
        // Check if username already exists
        LambdaQueryWrapper<User> usernameQuery = new LambdaQueryWrapper<>();
        usernameQuery.eq(User::getUsername, registerRequest.getUsername());
        if (userRepository.getOne(usernameQuery) != null || SYSTEM_USER.equals(registerRequest.getUsername())) {
            return Optional.empty();
        }

        // Check if email already exists
        LambdaQueryWrapper<User> emailQuery = new LambdaQueryWrapper<>();
        emailQuery.eq(User::getEmail, registerRequest.getEmail());
        if (userRepository.getOne(emailQuery) != null) {
            return Optional.empty();
        }

        // Create new user
        User user = new User();
        user.setUsername(registerRequest.getUsername());
        user.setEmail(registerRequest.getEmail());
        user.setFullName(registerRequest.getUsername());
        
        // Encode password
        BCryptPasswordEncoder encoder = new BCryptPasswordEncoder(10);
        user.setPasswordHash(encoder.encode(registerRequest.getPassword()));
        
        // Set default role and enabled status
        user.setRole("USER");
        user.setEnabled(true);
        
        // Save user
        userRepository.save(user);
        
        // Generate token
        String token = generateToken(user);
        user.setToken(token);
        
        return Optional.of(user);
    }
}
