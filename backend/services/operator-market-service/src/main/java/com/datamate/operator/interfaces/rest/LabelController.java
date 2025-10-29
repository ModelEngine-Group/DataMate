package com.datamate.operator.interfaces.rest;

import com.datamate.common.infrastructure.common.Response;
import com.datamate.common.interfaces.PagedResponse;
import com.datamate.operator.application.LabelService;
import com.datamate.operator.interfaces.dto.LabelDto;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/labels")
@RequiredArgsConstructor
public class LabelController {
    private final LabelService labelService;

    @GetMapping
    public ResponseEntity<Response<PagedResponse<LabelDto>>> labelsGet(@RequestParam("page") Integer page,
                                                                       @RequestParam("size") Integer size,
                                                                       @RequestParam("keyword") String keyword) {
        return ResponseEntity.ok(Response.ok(PagedResponse.of(labelService.getLabels(page, size, keyword))));
    }

    @PutMapping("/{id}")
    public ResponseEntity<Response<Object>> labelsIdPut(@PathVariable("id") String id,
                                                        @RequestBody List<LabelDto> updateLabelDtoRequest) {
        labelService.updateLabel(id, updateLabelDtoRequest);
        return ResponseEntity.ok(Response.ok(null));
    }

    @PostMapping
    public ResponseEntity<Response<Object>> labelsPost(@RequestBody LabelDto labelsPostRequest) {
        labelService.createLabels(labelsPostRequest);
        return ResponseEntity.ok(Response.ok(null));
    }
}


