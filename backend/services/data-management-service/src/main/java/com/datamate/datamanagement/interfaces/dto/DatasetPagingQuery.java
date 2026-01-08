package com.datamate.datamanagement.interfaces.dto;

import com.datamate.common.interfaces.PagingQuery;
import com.datamate.datamanagement.common.enums.DatasetStatusType;
import com.datamate.datamanagement.common.enums.DatasetType;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springaicommunity.mcp.annotation.McpToolParam;

import java.util.ArrayList;
import java.util.List;

/**
 * 数据集分页查询请求
 *
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class DatasetPagingQuery extends PagingQuery {
    /**
     * 数据集类型过滤
     */
    @McpToolParam(description = "数据集类型过滤，取值范围为text/image/video/audio/other", required = false)
    private DatasetType type;

    /**
     * 标签名过滤
     */
    @McpToolParam(description = "标签名过滤", required = false)
    private List<String> tags = new ArrayList<>();

    /**
     * 关键词搜索（名称或描述）
     */
    @McpToolParam(description = "关键词搜索（名称或描述）", required = false)
    private String keyword;

    /**
     * 状态过滤
     */
    @McpToolParam(description = "状态过滤", required = false)
    private DatasetStatusType status;
}
