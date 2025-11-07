package com.datamate.operator.interfaces.rest;

import com.datamate.common.interfaces.PagedResponse;
import com.datamate.operator.application.OperatorService;
import com.datamate.operator.domain.contants.OperatorConstant;
import com.datamate.operator.interfaces.dto.OperatorDto;
import com.datamate.operator.interfaces.dto.OperatorsListPostRequest;
import com.datamate.operator.interfaces.dto.UploadOperatorRequest;
import lombok.RequiredArgsConstructor;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/operators")
@RequiredArgsConstructor
public class OperatorController {
    private final OperatorService operatorService;

    @PostMapping("/list")
    public PagedResponse<OperatorDto> operatorsListPost(@RequestBody OperatorsListPostRequest request) {
        Boolean isStar = null;
        List<String> categories = request.getCategories();
        if (CollectionUtils.isNotEmpty(request.getCategories()) &&
                request.getCategories().contains(OperatorConstant.CATEGORY_STAR_ID)) {
            isStar = true;
            categories.remove(OperatorConstant.CATEGORY_STAR_ID);
        }
        List<OperatorDto> responses = operatorService.getOperators(request.getPage(), request.getSize(),
                categories, request.getOperatorName(), isStar);
        int count = operatorService.getOperatorsCount(categories, request.getOperatorName(), isStar);
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
    public OperatorDto operatorsUploadPost(@RequestBody UploadOperatorRequest request) {
        return operatorService.uploadOperator(request.getFileName());
    }

    @PostMapping(value = "/upload/pre-upload", produces = MediaType.APPLICATION_JSON_VALUE)
    public String preUpload() {
        return operatorService.preUpload();
    }

    @PostMapping("/upload/chunk")
    public void chunkUpload(@ModelAttribute UploadOperatorRequest request) {
        operatorService.chunkUpload(request);
    }

    @DeleteMapping("/{id}")
    public void operatorDelete(@PathVariable("id") String id) {
        operatorService.deleteOperator(id);
    }
}
