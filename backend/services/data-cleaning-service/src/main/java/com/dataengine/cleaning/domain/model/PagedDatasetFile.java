package com.dataengine.cleaning.domain.model;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;


@Getter
@Setter
@NoArgsConstructor
public class PagedDatasetFile {
    private List<DatasetFile> content;

    private Integer page;

    private Integer size;

    private Integer totalElements;

    private Integer totalPages;

    private Boolean first;

    private Boolean last;
}
