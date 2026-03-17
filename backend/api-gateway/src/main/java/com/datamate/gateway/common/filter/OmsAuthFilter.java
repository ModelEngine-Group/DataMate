package com.datamate.gateway.common.filter;

import com.datamate.gateway.common.config.SslIgnoreHttpClientFactory;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.apache.hc.client5.http.classic.methods.HttpPost;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.apache.hc.core5.http.ParseException;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.http.HttpCookie;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.util.MultiValueMap;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.io.IOException;
import java.util.List;
import java.util.Objects;

/**
 * OmsAuthFilter is a global filter that authenticates requests to the OMS service.
 * 
 * @author songyongtan
 * @date 2026-03-16
 */
@Slf4j
@Component
public class OmsAuthFilter implements GlobalFilter {
    private static final String USER_NAME_HEADER = "X-User-Name";
    private static final String AUTH_TOKEN_NEW_HEADER_KEY = "X-Auth-Token";
    private static final String CSRF_TOKEN_NEW_HEADER_KEY = "X-Csrf-Token";
    private static final String AUTH_TOKEN_KEY = "__Host-X-Auth-Token";
    private static final String CSRF_TOKEN_KEY = "__Host-X-Csrf-Token";

    private final Boolean omsAuthEnable;

    private final String omsServiceUrl;

    private final ObjectMapper objectMapper = new ObjectMapper();

    private final SslIgnoreHttpClientFactory sslIgnoreHttpClientFactory;

    private CloseableHttpClient httpClient;

    public OmsAuthFilter(
            @Value("${oms.auth.enabled:false}") Boolean omsAuthEnable,
            @Value("${oms.service.url}") String omsServiceUrl,
            SslIgnoreHttpClientFactory sslIgnoreHttpClientFactory) {
        log.info("OmsAuthFilter is apply, omsAuthEnable: {}", omsAuthEnable);
        this.omsAuthEnable = omsAuthEnable;
        this.omsServiceUrl = omsServiceUrl;
        this.sslIgnoreHttpClientFactory = sslIgnoreHttpClientFactory;
        try {
            this.httpClient = this.sslIgnoreHttpClientFactory.getHttpClient();
        } catch (Exception e) {
            log.error("Failed to create SSL ignore HTTP client", e);
        }
    }

    public void setHttpClient(CloseableHttpClient httpClient) {
        this.httpClient = httpClient;
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        if (!this.omsAuthEnable) {
            return chain.filter(exchange);
        }
        ServerHttpRequest request = exchange.getRequest();
        String uri = request.getURI().getPath();
        log.info("Oms auth filter uri: {}", uri);

        try {
            String userName = this.getUserNameFromOms(request);
            if (userName == null) {
                exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
                log.error("Authentication failed: Token is null or invalid.");
                return exchange.getResponse().setComplete();
            }
            ServerHttpRequest newRequest = request.mutate()
                    .header(USER_NAME_HEADER, userName)
                    .build();

            return chain.filter(exchange.mutate().request(newRequest).build());
        } catch (IOException | ParseException e) {
            log.error("Exception occurred during POST request: {}", e.getMessage(), e);
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }
    }

    private String getUserNameFromOms(ServerHttpRequest request) throws IOException, ParseException {
        String fullPath = this.omsServiceUrl + "/framework/v1/iam/roles/query-by-token";

        HttpPost httpPost = new HttpPost(fullPath);

        MultiValueMap<String, HttpCookie> cookies = request.getCookies();
        String authToken = getToken(cookies, AUTH_TOKEN_KEY);
        String csrfToken = getToken(cookies, CSRF_TOKEN_KEY);

        httpPost.setHeader(AUTH_TOKEN_NEW_HEADER_KEY, authToken);
        httpPost.setHeader(CSRF_TOKEN_NEW_HEADER_KEY, csrfToken);

        CloseableHttpResponse response = httpClient.execute(httpPost);
        String responseBody = EntityUtils.toString(response.getEntity());
        log.info("response code: {}, response body: {}", response.getCode(), responseBody);

        ResultVo<List<String>> resultVo = objectMapper.readValue(responseBody, 
            objectMapper.getTypeFactory().constructParametricType(ResultVo.class, List.class));

        if (resultVo.getData() == null || resultVo.getData().isEmpty()) {
            return null;
        }

        return resultVo.getData().get(0);
    }

    private String getToken(MultiValueMap<String, HttpCookie> cookies, String tokenKey) {
        if (cookies.containsKey(tokenKey)) {
            return Objects.requireNonNull(cookies.getFirst(tokenKey)).getValue();
        }
        return "";
    }

    @Data
    public static class ResultVo<T> {
        private Integer code;
        private String msg;
        private T data;
    }
}
