package com.datamate.main.filter;

import com.datamate.common.infrastructure.common.Response;
import com.datamate.common.infrastructure.config.DataScopeHandle;
import com.datamate.common.infrastructure.exception.CommonErrorCode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;

/**
 * 用户信息过滤器
 *
 * @since 2026/1/19
 */
@Slf4j
@Component
public class UserContextFilter implements Filter {
    private static final String USER_HEADER = "User";

    @Value("${datamate.jwt.enable:false}")
    private Boolean jwtEnable;

    @Override
    public void doFilter(ServletRequest servletRequest, ServletResponse servletResponse, FilterChain filterChain) {
        try {
            HttpServletRequest httpRequest = (HttpServletRequest) servletRequest;
            HttpServletResponse httpResponse = (HttpServletResponse) servletResponse;
            String user = httpRequest.getHeader(USER_HEADER);
            ObjectMapper objectMapper = new ObjectMapper();
            if (jwtEnable && StringUtils.isBlank(user)) {
                httpResponse.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                httpResponse.getWriter().write(objectMapper.writeValueAsString(Response.error(CommonErrorCode.UNAUTHORIZED)));
                return;
            }
            DataScopeHandle.setUserInfo(user);
            filterChain.doFilter(servletRequest, servletResponse);
        } catch (IOException | ServletException e) {
            log.error("Request failed!");
            throw new RuntimeException(e);
        } finally {
            DataScopeHandle.removeUserInfo();
        }
    }
}
