package com.datamate.gateway.infrastructure.client;

import java.io.IOException;

/**
 * OmsService is a service that interacts with the OMS service.
 * 
 * @author songyongtan
 * @date 2026-03-16
 */
public interface OmsService {
    /**
     * getUserNameFromOms gets the user name from the OMS service.
     * 
     * @param authToken the auth token
     * @param csrfToken the csrf token
     * @param realIp the real ip
     * @return the user name
     * @throws IOException if an error occurs
     */
    String getUserNameFromOms(String authToken, String csrfToken, String realIp);
}
