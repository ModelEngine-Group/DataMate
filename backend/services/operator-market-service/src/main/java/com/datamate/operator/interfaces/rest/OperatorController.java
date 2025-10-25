package com.datamate.operator.interfaces.rest;

import com.datamate.common.infrastructure.common.Response;
import com.datamate.common.interfaces.PagedResponse;
import com.datamate.operator.application.OperatorService;
import com.datamate.operator.interfaces.dto.OperatorDto;
import com.datamate.operator.interfaces.dto.OperatorsListPostRequest;
import com.datamate.operator.interfaces.dto.UploadOperatorRequest;
import jakarta.validation.Valid;
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
    public PagedResponse<OperatorDto> operatorsListPost(@RequestBody OperatorsListPostRequest request) {
        List<OperatorDto> responses = operatorService.getOperators(request.getPage(), request.getSize(),
                request.getCategories(), request.getOperatorName(), request.getIsStar());
        int count = operatorService.getOperatorsCount(request.getCategories(), request.getOperatorName(),
                request.getIsStar());
        int totalPages = (count + request.getSize() + 1) / request.getSize();
        return PagedResponse.of(responses, request.getPage(), count, totalPages);
    }

    @GetMapping("/{id}")
    public OperatorDto operatorsIdGet(@PathVariable("id") String id) {
        return operatorService.getOperatorById(id);
    }

    @PutMapping("/{id}")
    public OperatorDto operatorsIdPut(@PathVariable("id") String id,
                                                                @RequestBody OperatorDto updateOperatorRequest) {
        return operatorService.updateOperator(id, updateOperatorRequest);
    }

    @PostMapping("/create")
    public OperatorDto operatorsCreatePost(@RequestBody OperatorDto createOperatorRequest) {
        return operatorService.createOperator(createOperatorRequest);
    }

    @PostMapping("/upload")
    public OperatorDto operatorsUploadPost(@RequestPart(value = "file") MultipartFile file) {
        return operatorService.uploadOperator(file);
    }

    @PostMapping("/upload/pre-upload")
    public String preUpload() {
        return operatorService.preUpload();
    }

    @PostMapping("/upload/chunk")
    public void chunkUpload(@RequestBody UploadOperatorRequest request) {
        operatorService.chunkUpload(request);
    }
}
