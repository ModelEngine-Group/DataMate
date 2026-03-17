package com.datamate.gateway.common.filter;

import com.datamate.gateway.common.config.SslIgnoreHttpClientFactory;
import org.apache.hc.client5.http.classic.methods.HttpPost;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.apache.hc.core5.http.io.entity.StringEntity;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.http.HttpCookie;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.mock.http.server.reactive.MockServerHttpRequest;
import org.springframework.mock.web.server.MockServerWebExchange;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.nio.charset.StandardCharsets;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * OmsAuthFilterTest is a test class for OmsAuthFilter.
 *
 * @author songyongtan
 * @date 2026-03-16
 */
@ExtendWith(MockitoExtension.class)
class OmsAuthFilterTest {

    @Mock
    private GatewayFilterChain chain;

    @Mock
    private CloseableHttpClient httpClient;

    @Mock
    private CloseableHttpResponse httpResponse;

    @Mock
    private SslIgnoreHttpClientFactory sslIgnoreHttpClientFactory;

    private OmsAuthFilter omsAuthFilter;

    @BeforeEach
    void setUp() throws Exception {
        when(sslIgnoreHttpClientFactory.getHttpClient()).thenReturn(httpClient);
    }

    private OmsAuthFilter createOmsAuthFilter(Boolean omsAuthEnable) {
        return new OmsAuthFilter(omsAuthEnable, "http://localhost:8080", sslIgnoreHttpClientFactory);
    }

    @Test
    void testFilter_WhenOmsAuthDisabled_ShouldPassThrough() {
        omsAuthFilter = createOmsAuthFilter(false);

        MockServerHttpRequest request = MockServerHttpRequest.get("/api/test").build();
        ServerWebExchange exchange = MockServerWebExchange.from(request);

        when(chain.filter(any(ServerWebExchange.class))).thenReturn(Mono.empty());

        omsAuthFilter.filter(exchange, chain);

        verify(chain, times(1)).filter(any(ServerWebExchange.class));
    }

    @Test
    void testFilter_WhenOmsAuthEnabledAndTokenValid_ShouldAddUserNameHeader() throws Exception {
        omsAuthFilter = createOmsAuthFilter(true);

        MockServerHttpRequest request = MockServerHttpRequest.get("/api/test").build();
        ServerWebExchange exchange = MockServerWebExchange.from(request);

        String successResponse = "{\"code\":200,\"msg\":\"success\",\"data\":[\"testuser\"]}";
        StringEntity entity = new StringEntity(successResponse, StandardCharsets.UTF_8);
        when(httpResponse.getEntity()).thenReturn(entity);
        when(httpClient.execute(any(HttpPost.class))).thenReturn(httpResponse);

        when(chain.filter(any(ServerWebExchange.class))).thenReturn(Mono.empty());

        omsAuthFilter.filter(exchange, chain);

        verify(chain, times(1)).filter(argThat(ex -> {
            HttpHeaders headers = ex.getRequest().getHeaders();
            return headers.containsKey("X-User-Name") && 
                   "testuser".equals(headers.getFirst("X-User-Name"));
        }));
    }

    @Test
    void testFilter_WhenOmsAuthEnabledAndTokenInvalid_ShouldReturn401() throws Exception {
        omsAuthFilter = createOmsAuthFilter(true);

        MockServerHttpRequest request = MockServerHttpRequest.get("/api/test").build();
        ServerWebExchange exchange = MockServerWebExchange.from(request);

        String failureResponse = "{\"code\":403,\"msg\":\"unauthorized\",\"data\":[]}";
        StringEntity entity = new StringEntity(failureResponse, StandardCharsets.UTF_8);
        when(httpResponse.getEntity()).thenReturn(entity);
        when(httpClient.execute(any(HttpPost.class))).thenReturn(httpResponse);

        omsAuthFilter.filter(exchange, chain);

        ServerHttpResponse response = exchange.getResponse();
        assertEquals(HttpStatus.UNAUTHORIZED, response.getStatusCode());
        verify(chain, never()).filter(any(ServerWebExchange.class));
    }

    @Test
    void testFilter_WhenOmsAuthEnabledAndNoToken_ShouldReturn401() throws Exception {
        omsAuthFilter = createOmsAuthFilter(true);

        MockServerHttpRequest request = MockServerHttpRequest.get("/api/test").build();
        ServerWebExchange exchange = MockServerWebExchange.from(request);

        String failureResponse = "{\"code\":401,\"msg\":\"unauthorized\",\"data\":[]}";
        StringEntity entity = new StringEntity(failureResponse, StandardCharsets.UTF_8);
        when(httpResponse.getEntity()).thenReturn(entity);
        when(httpClient.execute(any(HttpPost.class))).thenReturn(httpResponse);

        omsAuthFilter.filter(exchange, chain);

        ServerHttpResponse response = exchange.getResponse();
        assertEquals(HttpStatus.UNAUTHORIZED, response.getStatusCode());
        verify(chain, never()).filter(any(ServerWebExchange.class));
    }

    @Test
    void testFilter_WhenOmsAuthEnabledAndTokenInCookie_ShouldUseToken() throws Exception {
        omsAuthFilter = createOmsAuthFilter(true);

        HttpCookie authCookie = new HttpCookie("__Host-X-Auth-Token", "test-token");
        MockServerHttpRequest request = MockServerHttpRequest.get("/api/test")
                .cookie(authCookie)
                .build();
        ServerWebExchange exchange = MockServerWebExchange.from(request);

        String successResponse = "{\"code\":200,\"msg\":\"success\",\"data\":[\"testuser\"]}";
        StringEntity entity = new StringEntity(successResponse, StandardCharsets.UTF_8);
        when(httpResponse.getEntity()).thenReturn(entity);
        when(httpClient.execute(any(HttpPost.class))).thenReturn(httpResponse);

        when(chain.filter(any(ServerWebExchange.class))).thenReturn(Mono.empty());

        omsAuthFilter.filter(exchange, chain);

        verify(chain, times(1)).filter(any(ServerWebExchange.class));
    }
}
