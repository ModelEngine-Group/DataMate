package com.dataengine.common.interfaces;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class PagedResponse <T> {
    private int page;
    private int size;
    private long totalElements;
    private int totalPages;
    private List<T> content;

    public PagedResponse(List<T> content) {
        this.page = 0;
        this.size = content.size();
        this.totalElements = content.size();
        this.totalPages = 1;
        this.content = content;
    }

    public static <T> PagedResponse<T> of(List<T> content) {
        return new PagedResponse<>(content);
    }
}
