package com.datamate.gateway.infrastructure.client.impl;

import com.datamate.gateway.common.config.SslIgnoreHttpClientFactory;
import com.datamate.gateway.infrastructure.client.OmsExtensionService;
import com.datamate.gateway.infrastructure.client.dto.ResourceGroup;
import com.datamate.gateway.infrastructure.client.dto.Resp;
import com.fasterxml.jackson.databind.JavaType;
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
import java.util.List;

/**
 * OmsExtensionServiceImpl is an implementation of OmsExtensionService.
 *
 * @author MoeexT
 * @since 2026-03-17
 */
@Slf4j
@Service
public class OmsExtensionServiceImpl implements OmsExtensionService {
    @Value("${OMS_EXTENSION_URL:https://oms-extension:8021}")
    private final String omsExtensionUrl;

    private final ObjectMapper objectMapper;

    private CloseableHttpClient httpClient;

    public OmsExtensionServiceImpl(@Value("${oms.service.url}") String omsExtensionUrl, ObjectMapper objectMapper,
        SslIgnoreHttpClientFactory sslIgnoreHttpClientFactory) {
        this.omsExtensionUrl = omsExtensionUrl;
        this.objectMapper = objectMapper;
        try {
            this.httpClient = sslIgnoreHttpClientFactory.getHttpClient();
        } catch (Exception e) {
            log.error("Failed to create SSL ignore HTTP client", e);
        }
    }

    /**
     * Get the group ID of the user's user group
     *
     * @param userName the username
     * @return resource-group-id of this user
     */
    @Override
    public String getUserGroupId(String userName) {
        try {
            String fullPath = this.omsExtensionUrl + "/ui/v1/resource-groups/user/" + userName + "/resource-group";
            HttpGet httpGet = new HttpGet(fullPath);
            CloseableHttpResponse response = httpClient.execute(httpGet);
            String responseBody = EntityUtils.toString(response.getEntity());
            log.info("response code: {}, response body: {}", response.getCode(), responseBody);

            JavaType listType = objectMapper.getTypeFactory()
                .constructParametricType(List.class, ResourceGroup.class);
            JavaType respType = objectMapper.getTypeFactory()
                .constructParametricType(Resp.class, listType);
            Resp<List<ResourceGroup>> resp = objectMapper.readValue(responseBody,
                objectMapper.getTypeFactory().constructParametricType(Resp.class, respType));

            if (resp.data() == null || resp.data().isEmpty()) {
                return null;
            }

            return resp.data().getFirst().getId();
        } catch (IOException | ParseException e) {
            log.error("Failed to get user name from OMS service", e);
            return null;
        }
    }
}
