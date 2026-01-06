package com.datamate.operator.interfaces.rest;

import com.datamate.common.infrastructure.common.IgnoreResponseWrap;
import com.datamate.common.interfaces.PagedResponse;
import com.datamate.operator.application.OperatorService;
import com.datamate.operator.interfaces.dto.OperatorDto;
import com.datamate.operator.interfaces.dto.OperatorsListPostRequest;
import com.datamate.operator.interfaces.dto.UploadOperatorRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.File;
import java.util.List;

@RestController
@RequestMapping("/operators")
@RequiredArgsConstructor
public class OperatorController {
    private final OperatorService operatorService;

    @PostMapping("/list")
    public PagedResponse<OperatorDto> operatorsListPost(@RequestBody OperatorsListPostRequest request) {
        List<List<String>> categories = request.getCategories();
        List<OperatorDto> responses = operatorService.getOperators(request.getPage(), request.getSize(),
                categories, request.getKeyword(), request.getIsStar());
        int count = operatorService.getOperatorsCount(categories, request.getKeyword(), request.getIsStar());
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

    @IgnoreResponseWrap
    @GetMapping(value = "/examples/download", produces = MediaType.APPLICATION_OCTET_STREAM_VALUE + ";charset=UTF-8")
    public ResponseEntity<Resource> downloadDatasetFileById() {
        try {
            File file = new File("/opt/backend/test_operator.tar");
            Resource resource = operatorService.downloadExampleOperator(file);
            return ResponseEntity.ok()
                    .contentType(MediaType.APPLICATION_OCTET_STREAM)
                    .header(HttpHeaders.ACCESS_CONTROL_EXPOSE_HEADERS, HttpHeaders.CONTENT_DISPOSITION)
                    .header(HttpHeaders.CONTENT_DISPOSITION,
                            "attachment; filename=\"" + file.getName() + "\"")
                    .body(resource);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
