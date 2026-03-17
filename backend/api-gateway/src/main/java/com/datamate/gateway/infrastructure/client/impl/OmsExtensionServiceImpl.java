package com.datamate.gateway.infrastructure.client.impl;

import com.datamate.gateway.infrastructure.client.OmsExtensionService;
import org.springframework.stereotype.Service;

/**
 * OmsExtensionServiceImpl is an implementation of OmsExtensionService.
 * 
 * @author songyongtan
 * @date 2026-03-17
 */
@Service
public class OmsExtensionServiceImpl implements OmsExtensionService {
    @Override
    public String getUserGroupId(String userName) {
        return userName;
    }
}
