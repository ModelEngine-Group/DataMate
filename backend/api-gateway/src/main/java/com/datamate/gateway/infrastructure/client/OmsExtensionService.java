package com.datamate.gateway.infrastructure.client;

/**
 * OmsExtensionService is a service interface for OMS extension operations.
 * 
 * @author songyongtan
 * @date 2026-03-17
 */
public interface OmsExtensionService {
    /**
     * getUserGroupId gets the user group ID by user name.
     * 
     * @param userName the user name
     * @return the user group ID
     */
    String getUserGroupId(String userName);
}
