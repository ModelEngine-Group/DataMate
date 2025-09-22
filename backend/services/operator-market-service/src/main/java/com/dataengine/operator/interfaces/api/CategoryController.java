package com.dataengine.operator.interfaces.api;

import com.dataengine.operator.domain.modal.Category;
import com.dataengine.operator.interfaces.dto.*;
import com.dataengine.operator.application.CategoryService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RestController;
import java.util.List;
import java.util.Map;

@RestController
public class CategoryController implements CategoryApi {
    @Autowired
    private CategoryService categoryService;


    @Override
    public ResponseEntity<List<CategoryTreeGet200ResponseInner>> categoryTreeGet() {
        return ResponseEntity.ok(categoryService.getAllCategories());
    }
}
