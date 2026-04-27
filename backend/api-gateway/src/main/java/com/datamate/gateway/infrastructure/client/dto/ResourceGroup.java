/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2026-2026. All rights reserved.
 */

package com.datamate.gateway.infrastructure.client.dto;

import lombok.Getter;

import java.time.LocalDateTime;

/**
 * 资源组信息
 */
@Getter
public class ResourceGroup {
    private String id;

    private String parentId;

    private String name;

    private String description;

    private LocalDateTime createTime;

    private LocalDateTime updateTime;

    private boolean isDeleted;

    private boolean isBuiltin;
}
