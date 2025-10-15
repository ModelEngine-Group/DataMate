package com.dataengine.operator.interfaces.api;

import com.dataengine.common.interfaces.PagedResponse;

import com.dataengine.common.interfaces.Response;
import com.dataengine.operator.application.CategoryService;
import com.dataengine.operator.interfaces.dto.CategoryTreeResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;


@RestController
@RequestMapping("/categories")
@RequiredArgsConstructor
public class CategoryController {
    private final CategoryService categoryService;

    @GetMapping("/tree")
    public ResponseEntity<Response<PagedResponse<CategoryTreeResponse>>> categoryTreeGet() {
        List<CategoryTreeResponse> allCategories = categoryService.getAllCategories();
        return ResponseEntity.ok(Response.ok(PagedResponse.of(allCategories)));
    }
}
