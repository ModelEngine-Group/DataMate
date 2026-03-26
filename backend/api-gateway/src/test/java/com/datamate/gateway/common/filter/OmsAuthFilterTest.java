package com.datamate.gateway.common.filter;

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

import com.datamate.gateway.infrastructure.client.OmsExtensionService;
import com.datamate.gateway.infrastructure.client.OmsService;

import reactor.core.publisher.Mono;

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
    private OmsService omsService;

    @Mock
    private OmsExtensionService omsExtensionService;

    private OmsAuthFilter omsAuthFilter;

    @BeforeEach
    void setUp() throws Exception {
    }

    private OmsAuthFilter createOmsAuthFilter(Boolean omsAuthEnable) {
        return new OmsAuthFilter(omsAuthEnable, omsService, omsExtensionService);
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

        when(omsService.getUserNameFromOms(anyString(), anyString(), anyString())).thenReturn("testuser");
        when(omsExtensionService.getUserGroupId("testuser")).thenReturn("testuser");

        when(chain.filter(any(ServerWebExchange.class))).thenReturn(Mono.empty());

        omsAuthFilter.filter(exchange, chain);

        verify(chain, times(1)).filter(argThat(ex -> {
            HttpHeaders headers = ex.getRequest().getHeaders();
            return headers.containsKey("X-User-Name") && 
                   "testuser".equals(headers.getFirst("X-User-Name")) &&
                   headers.containsKey("X-User-Group-Id") &&
                   "testuser".equals(headers.getFirst("X-User-Group-Id"));
        }));
    }

    @Test
    void testFilter_WhenOmsAuthEnabledAndTokenInvalid_ShouldReturn401() throws Exception {
        omsAuthFilter = createOmsAuthFilter(true);

        MockServerHttpRequest request = MockServerHttpRequest.get("/api/test").build();
        ServerWebExchange exchange = MockServerWebExchange.from(request);

        when(omsService.getUserNameFromOms(anyString(), anyString(), anyString())).thenReturn(null);

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

        when(omsService.getUserNameFromOms(anyString(), anyString(), anyString())).thenReturn(null);

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

        when(omsService.getUserNameFromOms(anyString(), anyString(), anyString())).thenReturn("testuser");

        when(chain.filter(any(ServerWebExchange.class))).thenReturn(Mono.empty());

        omsAuthFilter.filter(exchange, chain);

        verify(chain, times(1)).filter(any(ServerWebExchange.class));
    }
}
