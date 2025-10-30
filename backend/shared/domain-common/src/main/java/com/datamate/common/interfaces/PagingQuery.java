package com.datamate.common.interfaces;

import lombok.Getter;

@Getter
public class PagingQuery {
    /**
     * 页码，从0开始
     */
    private Integer page = 0;

    /**
     * 每页大小
     */
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
}
