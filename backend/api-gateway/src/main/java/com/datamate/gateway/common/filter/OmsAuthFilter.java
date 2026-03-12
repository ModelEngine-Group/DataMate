package com.datamate.gateway.common.filter;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.hc.client5.http.classic.methods.HttpPost;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.core5.http.ParseException;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.filter.GatewayFilter;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.OrderedGatewayFilter;
import org.springframework.cloud.gateway.filter.factory.AbstractGatewayFilterFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.io.IOException;
import java.util.List;

@Slf4j
@Component
@RequiredArgsConstructor
public class OmsAuthFilter extends AbstractGatewayFilterFactory<OmsAuthFilter.Config> {
    private static final int OMS_AUTH_FILTER_ORDER = -1;
    private static final String USER_NAME_HEADER = "X-User-Name";

    @Value("${oms.auth.enabled:false}")
    private Boolean omsAuthEnable;

    @Value("${oms.gateway.url}")
    private String omsGatewayUrl;

    private final ObjectMapper objectMapper;

    private CloseableHttpClient httpClient;

    public OmsAuthFilter() {
        super(Config.class);
        this.objectMapper = new ObjectMapper();
        this.httpClient = HttpClients.createDefault();
    }

    public void setHttpClient(CloseableHttpClient httpClient) {
        this.httpClient = httpClient;
    }

    @Override
    public GatewayFilter apply(Config config) {
        log.info("OmsAuthFilter is apply, omsAuthEnable: {}", omsAuthEnable);
        return new OrderedGatewayFilter(this::filter, OMS_AUTH_FILTER_ORDER);
    }

    private Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        if (!omsAuthEnable) {
            return chain.filter(exchange);
        }
        ServerHttpRequest request = exchange.getRequest();
        String uri = request.getURI().getPath();
        log.info("Oms auth filter uri: {}", uri);

        String fullPath = omsGatewayUrl + "/framework/v1/iam/roles/query-by-token";
        log.info("oms auth full path: {}", fullPath);

        try {
            HttpPost httpPost = new HttpPost(fullPath);

            String authToken = request.getHeaders().getFirst("Authorization");
            if (authToken != null && authToken.startsWith("Bearer ")) {
                authToken = authToken.substring(7);
            }
            httpPost.setHeader("X-Auth-Token", authToken);

            CloseableHttpResponse response = httpClient.execute(httpPost);
            String responseBody = EntityUtils.toString(response.getEntity());
            log.info("response code: {}, response body: {}", response.getCode(), responseBody);

            ResultVo<List<String>> resultVo = objectMapper.readValue(responseBody, 
                objectMapper.getTypeFactory().constructParametricType(ResultVo.class, List.class));

            if (resultVo.getData() == null || resultVo.getData().isEmpty()) {
                exchange.getResponse().setStatusCode(HttpStatus.FORBIDDEN);
                log.error("Authentication failed: Token is null or invalid.");
                return exchange.getResponse().setComplete();
            }

            String userName = resultVo.getData().get(0);
            ServerHttpRequest newRequest = request.mutate()
                    .header(USER_NAME_HEADER, userName)
                    .build();

            return chain.filter(exchange.mutate().request(newRequest).build());
        } catch (IOException | ParseException e) {
            log.error("Exception occurred during POST request: {}", e.getMessage(), e);
            exchange.getResponse().setStatusCode(HttpStatus.FORBIDDEN);
            return exchange.getResponse().setComplete();
        }
    }

    @Data
    @NoArgsConstructor
    public static class Config {}

    @Data
    public static class ResultVo<T> {
        private Integer code;
        private String message;
        private T data;
    }
}
