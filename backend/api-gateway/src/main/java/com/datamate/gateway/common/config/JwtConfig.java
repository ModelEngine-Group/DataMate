package com.datamate.gateway.common.config;

import jakarta.annotation.PostConstruct;
import lombok.Getter;
import lombok.Setter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * JwtConfig
 *
 * @since 2026/1/14
 */
@Getter
@Setter
@Slf4j
@Configuration
@ConfigurationProperties(prefix = "datamate.jwt")
public class JwtConfig {
    private String secret;

    @PostConstruct
    public void validate() {
        if (secret == null || secret.trim().isEmpty()) {
            throw new IllegalStateException(
                    """
                        JWT secret is required. Please configure datamate.jwt.secret
                        Options:
                        1. Add to application.yml:
                           datamate:
                             jwt:
                               secret: your-strong-secret-key-here
                        2. Set environment variable:
                           export JWT_SECRET=your-strong-secret-key-here
                        3. Run with system property:
                           -Ddatamate.jwt.secret=your-strong-secret-key-here"""
            );
        }

        // 额外验证
        if (secret.length() < 32) {
            log.warn("\n⚠️ JWT secret is only {} characters. For security, use at least 32 characters.\n", secret.length());
        }
    }
}
