package com.datamate.gateway.common.filter;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.hc.client5.http.classic.methods.HttpPost;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.apache.hc.core5.http.HttpEntity;
import org.apache.hc.core5.http.io.entity.StringEntity;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.cloud.gateway.filter.GatewayFilter;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.mock.http.server.reactive.MockServerHttpRequest;
import org.springframework.mock.web.server.MockServerWebExchange;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class OmsAuthFilterTest {

    @Mock
    private GatewayFilterChain chain;

    @Mock
    private CloseableHttpClient httpClient;

    @Mock
    private CloseableHttpResponse httpResponse;

    private OmsAuthFilter omsAuthFilter;
    private GatewayFilter gatewayFilter;

    @BeforeEach
    void setUp() throws Exception {
        omsAuthFilter = new OmsAuthFilter();
        setField(omsAuthFilter, "omsAuthEnable", false);
        setField(omsAuthFilter, "omsGatewayUrl", "http://localhost:8080");
        gatewayFilter = omsAuthFilter.apply(new OmsAuthFilter.Config());
    }

    private void setField(Object target, String fieldName, Object value) throws Exception {
        Field field = target.getClass().getDeclaredField(fieldName);
        field.setAccessible(true);
        field.set(target, value);
    }

    @Test
    void testFilter_WhenOmsAuthDisabled_ShouldPassThrough() {
        MockServerHttpRequest request = MockServerHttpRequest.get("/api/test").build();
        ServerWebExchange exchange = MockServerWebExchange.from(request);

        when(chain.filter(any(ServerWebExchange.class))).thenReturn(Mono.empty());

        gatewayFilter.filter(exchange, chain);

        verify(chain, times(1)).filter(any(ServerWebExchange.class));
    }

    @Test
    void testFilter_WhenOmsAuthEnabledAndTokenValid_ShouldAddUserNameHeader() throws Exception {
        setField(omsAuthFilter, "omsAuthEnable", true);
        omsAuthFilter.setHttpClient(httpClient);
        gatewayFilter = omsAuthFilter.apply(new OmsAuthFilter.Config());

        MockServerHttpRequest request = MockServerHttpRequest.get("/api/test")
                .header("Authorization", "Bearer valid-token")
                .build();
        ServerWebExchange exchange = MockServerWebExchange.from(request);

        String successResponse = "{\"code\":200,\"message\":\"success\",\"data\":[\"testuser\"]}";
        StringEntity entity = new StringEntity(successResponse, StandardCharsets.UTF_8);
        when(httpResponse.getEntity()).thenReturn(entity);
        when(httpClient.execute(any(HttpPost.class))).thenReturn(httpResponse);

        when(chain.filter(any(ServerWebExchange.class))).thenReturn(Mono.empty());

        gatewayFilter.filter(exchange, chain);

        verify(chain, times(1)).filter(argThat(ex -> {
            HttpHeaders headers = ex.getRequest().getHeaders();
            return headers.containsKey("X-User-Name") && 
                   "testuser".equals(headers.getFirst("X-User-Name"));
        }));
    }

    @Test
    void testFilter_WhenOmsAuthEnabledAndTokenInvalid_ShouldReturn403() throws Exception {
        setField(omsAuthFilter, "omsAuthEnable", true);
        omsAuthFilter.setHttpClient(httpClient);
        gatewayFilter = omsAuthFilter.apply(new OmsAuthFilter.Config());

        MockServerHttpRequest request = MockServerHttpRequest.get("/api/test")
                .header("Authorization", "Bearer invalid-token")
                .build();
        ServerWebExchange exchange = MockServerWebExchange.from(request);

        String failureResponse = "{\"code\":403,\"message\":\"unauthorized\",\"data\":[]}";
        StringEntity entity = new StringEntity(failureResponse, StandardCharsets.UTF_8);
        when(httpResponse.getEntity()).thenReturn(entity);
        when(httpClient.execute(any(HttpPost.class))).thenReturn(httpResponse);

        gatewayFilter.filter(exchange, chain);

        ServerHttpResponse response = exchange.getResponse();
        assertEquals(HttpStatus.FORBIDDEN, response.getStatusCode());
        verify(chain, never()).filter(any(ServerWebExchange.class));
    }

    @Test
    void testFilter_WhenOmsAuthEnabledAndNoToken_ShouldReturn403() throws Exception {
        setField(omsAuthFilter, "omsAuthEnable", true);
        omsAuthFilter.setHttpClient(httpClient);
        gatewayFilter = omsAuthFilter.apply(new OmsAuthFilter.Config());

        MockServerHttpRequest request = MockServerHttpRequest.get("/api/test").build();
        ServerWebExchange exchange = MockServerWebExchange.from(request);

        String failureResponse = "{\"code\":403,\"message\":\"unauthorized\",\"data\":[]}";
        StringEntity entity = new StringEntity(failureResponse, StandardCharsets.UTF_8);
        when(httpResponse.getEntity()).thenReturn(entity);
        when(httpClient.execute(any(HttpPost.class))).thenReturn(httpResponse);

        gatewayFilter.filter(exchange, chain);

        ServerHttpResponse response = exchange.getResponse();
        assertEquals(HttpStatus.FORBIDDEN, response.getStatusCode());
        verify(chain, never()).filter(any(ServerWebExchange.class));
    }

    @Test
    void testFilter_WhenOmsAuthEnabledAndBearerTokenFormat_ShouldExtractToken() throws Exception {
        setField(omsAuthFilter, "omsAuthEnable", true);
        omsAuthFilter.setHttpClient(httpClient);
        gatewayFilter = omsAuthFilter.apply(new OmsAuthFilter.Config());

        MockServerHttpRequest request = MockServerHttpRequest.get("/api/test")
                .header("Authorization", "Bearer test-token")
                .build();
        ServerWebExchange exchange = MockServerWebExchange.from(request);

        String successResponse = "{\"code\":200,\"message\":\"success\",\"data\":[\"testuser\"]}";
        StringEntity entity = new StringEntity(successResponse, StandardCharsets.UTF_8);
        when(httpResponse.getEntity()).thenReturn(entity);
        when(httpClient.execute(any(HttpPost.class))).thenReturn(httpResponse);

        when(chain.filter(any(ServerWebExchange.class))).thenReturn(Mono.empty());

        gatewayFilter.filter(exchange, chain);

        verify(chain, times(1)).filter(any(ServerWebExchange.class));
    }

    @Test
    void testFilter_WhenOmsAuthEnabledAndNonBearerToken_ShouldProcessAsIs() throws Exception {
        setField(omsAuthFilter, "omsAuthEnable", true);
        omsAuthFilter.setHttpClient(httpClient);
        gatewayFilter = omsAuthFilter.apply(new OmsAuthFilter.Config());

        MockServerHttpRequest request = MockServerHttpRequest.get("/api/test")
                .header("Authorization", "test-token")
                .build();
        ServerWebExchange exchange = MockServerWebExchange.from(request);

        String successResponse = "{\"code\":200,\"message\":\"success\",\"data\":[\"testuser\"]}";
        StringEntity entity = new StringEntity(successResponse, StandardCharsets.UTF_8);
        when(httpResponse.getEntity()).thenReturn(entity);
        when(httpClient.execute(any(HttpPost.class))).thenReturn(httpResponse);

        when(chain.filter(any(ServerWebExchange.class))).thenReturn(Mono.empty());

        gatewayFilter.filter(exchange, chain);

        verify(chain, times(1)).filter(any(ServerWebExchange.class));
    }
}
