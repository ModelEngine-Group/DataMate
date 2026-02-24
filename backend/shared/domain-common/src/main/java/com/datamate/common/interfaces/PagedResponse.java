package com.datamate.common.interfaces;

import com.baomidou.mybatisplus.core.metadata.IPage;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@NoArgsConstructor
public class PagedResponse<T> {
    // 当前页码（从 1 开始）
    private long page;
    // 每页数量
    private long size;
    private long totalElements;
    private long totalPages;
    private List<T> content;

    private PagedResponse(long page, long size, long totalElements, long totalPages, List<T> content) {
        this.page = page;
        this.size = size;
        this.totalElements = totalElements;
        this.totalPages = totalPages;
        this.content = content;
    }

    public static <T> PagedResponse<T> of(long page, long size, long totalElements, long totalPages, List<T> content) {
        return new PagedResponse<>(page, size, totalElements, totalPages, content);
    }

    public static <T> PagedResponse<T> of(IPage<T> page) {
        return new PagedResponse<>(page.getCurrent(), page.getSize(), page.getTotal(), page.getPages(), page.getRecords());
    }
}
