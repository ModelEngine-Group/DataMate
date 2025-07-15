package com.edatamate.common.dataset.dto;

import com.edatamate.common.dataset.DatasetStatus;
import com.edatamate.common.dataset.DatasetType;

public record DatasetPageQueryDto(
    Integer pageNum,
    Integer pageSize,
    String name,
    DatasetType type,
    DatasetStatus status,
    String createdBy
    // 可根据Dataset类补充其他查询字段
) {}
