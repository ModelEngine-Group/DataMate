package com.dataengine.common.interfaces;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class PagingQuery {

    /**
     * 页码，从0开始
     */
    private Integer page = 0;

    /**
     * 每页大小
     */
    private Integer size = 20;

    /**
     * 初始化分页参数
     */
    public void initPaging() {
        page = page == null ? 0 : page;
        size = size == null ? 20 : size;
    }
}
