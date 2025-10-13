package com.dataengine.cleaning.domain.model;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;


@Getter
@Setter
@NoArgsConstructor
public class PagedDatasetFileResponse {
    /** 文件内容列表 */
    private List<DatasetFileResponse> content;
    /** 当前页码 */
    private Integer page;
    /** 每页大小 */
    private Integer size;
    /** 总元素数 */
    private Integer totalElements;
    /** 总页数 */
    private Integer totalPages;
    /** 是否为第一页 */
    private Boolean first;
    /** 是否为最后一页 */
    private Boolean last;
}
