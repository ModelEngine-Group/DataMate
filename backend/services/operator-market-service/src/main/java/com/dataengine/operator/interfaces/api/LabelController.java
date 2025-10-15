package com.dataengine.operator.interfaces.api;

import com.dataengine.common.interfaces.PagedResponse;
import com.dataengine.common.interfaces.Response;
import com.dataengine.operator.application.LabelService;
import com.dataengine.operator.interfaces.dto.Label;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/labels")
@RequiredArgsConstructor
public class LabelController {
    private final LabelService labelService;

    @GetMapping
    public ResponseEntity<Response<PagedResponse<Label>>> labelsGet(@RequestParam("page") Integer page,
                                                                    @RequestParam("size") Integer size,
                                                                    @RequestParam("keyword") String keyword) {
        return ResponseEntity.ok(Response.ok(PagedResponse.of(labelService.getLabels(page, size, keyword))));
    }

    @PutMapping("/{id}")
    public ResponseEntity<Response<Object>> labelsIdPut(@PathVariable("id") String id,
                                                        @RequestBody List<Label> updateLabelRequest) {
        labelService.updateLabel(id, updateLabelRequest);
        return ResponseEntity.ok(Response.ok(null));
    }

    @PostMapping
    public ResponseEntity<Response<Object>> labelsPost(@RequestBody Label labelsPostRequest) {
        labelService.createLabels(labelsPostRequest);
        return ResponseEntity.ok(Response.ok(null));
    }
}


