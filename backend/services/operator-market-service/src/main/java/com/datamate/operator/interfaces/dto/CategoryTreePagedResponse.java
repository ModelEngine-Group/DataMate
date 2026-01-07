package com.datamate.operator.interfaces.dto;

import com.datamate.common.interfaces.PagedResponse;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@AllArgsConstructor
public class CategoryTreePagedResponse extends PagedResponse<CategoryTreeResponse> {
    Integer starCount;

    public CategoryTreePagedResponse(List<CategoryTreeResponse> content, Integer starCount) {
        super(content);
        this.starCount = starCount;
    }

    public static CategoryTreePagedResponse of(List<CategoryTreeResponse> content, Integer starCount) {
        return new CategoryTreePagedResponse(content, starCount);
    }
}
