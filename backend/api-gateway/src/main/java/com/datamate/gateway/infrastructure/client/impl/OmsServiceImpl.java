package com.datamate.gateway.infrastructure.client.impl;

import com.alibaba.fastjson2.JSON;
import com.alibaba.fastjson2.JSONException;
import com.alibaba.fastjson2.JSONObject;
import com.datamate.gateway.common.config.SslIgnoreHttpClientFactory;
import com.datamate.gateway.infrastructure.client.OmsService;
import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.extern.slf4j.Slf4j;

import org.apache.hc.client5.http.classic.methods.HttpGet;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.apache.hc.core5.http.ParseException;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;

/**
 * OmsServiceImpl is a service that interacts with the OMS service.
 *
 * @author songyongtan
 * @date 2026-03-16
 */
@Slf4j
@Service
public class OmsServiceImpl implements OmsService {
    private static final String AUTH_TOKEN_NEW_HEADER_KEY = "X-Auth-Token";
    private static final String CSRF_TOKEN_NEW_HEADER_KEY = "X-Csrf-Token";
    private static final String REAL_IP_HEADER_KEY = "X-Real-IP";

    @Value("${oms.service.url}")
    private final String omsServiceUrl;

    private final ObjectMapper objectMapper;

    private final SslIgnoreHttpClientFactory sslIgnoreHttpClientFactory;

    private CloseableHttpClient httpClient;

    public OmsServiceImpl(
            @Value("${oms.service.url}") String omsServiceUrl,
            ObjectMapper objectMapper,
            SslIgnoreHttpClientFactory sslIgnoreHttpClientFactory) {
        this.omsServiceUrl = omsServiceUrl;
        this.objectMapper = objectMapper;
        this.sslIgnoreHttpClientFactory = sslIgnoreHttpClientFactory;
        try {
            this.httpClient = this.sslIgnoreHttpClientFactory.getHttpClient();
        } catch (Exception e) {
            log.error("Failed to create SSL ignore HTTP client", e);
        }
    }

    @Override
    public String getUserNameFromOms(String authToken, String csrfToken, String realIp) {
        try {
            String fullPath = this.omsServiceUrl + "/framework/v1/sessions/current";
            HttpGet httpPost = new HttpGet(fullPath);
            httpPost.setHeader(AUTH_TOKEN_NEW_HEADER_KEY, authToken);
            httpPost.setHeader(CSRF_TOKEN_NEW_HEADER_KEY, csrfToken);
            httpPost.setHeader(REAL_IP_HEADER_KEY, realIp);

            CloseableHttpResponse response = httpClient.execute(httpPost);
            String responseBody = EntityUtils.toString(response.getEntity());

            try {
                JSONObject jsonObject = JSON.parseObject(responseBody);
                JSONObject data = jsonObject.getJSONObject("data");
                return  data.getString("userName");
            } catch (JSONException e) {
                log.error("Failed to parse response body: {}", e.getMessage());
                return null;
            }
        } catch (IOException | ParseException e) {
            log.error("Failed to get user name from OMS service", e);
            return null;
        }
    }
}
