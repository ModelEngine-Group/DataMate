package com.datamate.operator.interfaces.rest;

import com.datamate.common.infrastructure.common.Response;
import com.datamate.common.interfaces.PagedResponse;
import com.datamate.operator.application.OperatorService;
import com.datamate.operator.interfaces.dto.OperatorDto;
import com.datamate.operator.interfaces.dto.OperatorsListPostRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
@RequestMapping("/operators")
@RequiredArgsConstructor
public class OperatorController {
    private final OperatorService operatorService;

    @PostMapping("/list")
    public ResponseEntity<Response<PagedResponse<OperatorDto>>> operatorsListPost(@RequestBody OperatorsListPostRequest request) {
        List<OperatorDto> responses = operatorService.getOperators(request.getPage(), request.getSize(),
                request.getCategories(), request.getOperatorName(), request.getIsStar());
        int count = operatorService.getOperatorsCount(request.getCategories(), request.getOperatorName(),
                request.getIsStar());
        int totalPages = (count + request.getSize() + 1) / request.getSize();
        return ResponseEntity.ok(Response.ok(PagedResponse.of(responses, request.getPage(), count, totalPages)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<Response<OperatorDto>> operatorsIdGet(@PathVariable("id") String id) {
        return ResponseEntity.ok(Response.ok(operatorService.getOperatorById(id)));
    }

    @PutMapping("/{id}")
    public ResponseEntity<Response<OperatorDto>> operatorsIdPut(@PathVariable("id") String id,
                                                                @RequestBody OperatorDto updateOperatorRequest) {
        return ResponseEntity.ok(Response.ok(operatorService.updateOperator(id, updateOperatorRequest)));
    }

    @PostMapping("/create")
    public ResponseEntity<Response<OperatorDto>> operatorsCreatePost(@RequestBody OperatorDto createOperatorRequest) {
        return ResponseEntity.ok(Response.ok(operatorService.createOperator(createOperatorRequest)));
    }

    @PostMapping("/upload")
    public ResponseEntity<Response<OperatorDto>> operatorsUploadPost(@RequestPart(value = "file") MultipartFile file,
                                                                     @RequestParam(value = "description") String description) {
        return ResponseEntity.ok(Response.ok(operatorService.uploadOperator(file, description)));
    }
}
