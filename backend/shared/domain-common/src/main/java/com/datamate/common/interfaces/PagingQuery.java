package com.datamate.common.interfaces;

import lombok.Getter;
import lombok.NoArgsConstructor;
import org.springaicommunity.mcp.annotation.McpToolParam;

@Getter
@NoArgsConstructor
public class PagingQuery {
    /**
     * 页码，从0开始
     */
    @McpToolParam(description = "页码，从0开始")
    private Integer page = 0;

    /**
     * 每页大小
     */
    @McpToolParam(description = "每页大小")
    private Integer size = 20;

    public void setPage(Integer page) {
        if (page == null || page < 0) {
            this.page = 0;
        } else {
            this.page = page;
        }
    }
    public void setSize(Integer size) {
        if (size == null || size <= 0) {
            this.size = 20;
        } else {
            this.size = size;
        }
    }

    public PagingQuery(Integer page, Integer size) {
        setPage(page);
        setSize(size);
    }
}
