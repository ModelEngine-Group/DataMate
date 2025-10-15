package com.dataengine.operator.interfaces.api;

import com.dataengine.common.interfaces.PagedResponse;
import com.dataengine.common.interfaces.Response;
import com.dataengine.operator.application.OperatorService;
import com.dataengine.operator.interfaces.dto.CreateOperatorRequest;
import com.dataengine.operator.interfaces.dto.OperatorResponse;
import com.dataengine.operator.interfaces.dto.OperatorsListPostRequest;
import com.dataengine.operator.interfaces.dto.UpdateOperatorRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
@RequestMapping("/operators")
@RequiredArgsConstructor
public class OperatorController {
    private final OperatorService operatorService;

    @PostMapping("/list")
    public ResponseEntity<Response<PagedResponse<OperatorResponse>>> operatorsListPost(@RequestBody OperatorsListPostRequest request) {
        List<OperatorResponse> responses = operatorService.getOperators(request.getPage(), request.getSize(),
                request.getCategories(), request.getOperatorName(), request.getIsStar());
        return ResponseEntity.ok(Response.ok(PagedResponse.of(responses)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<Response<OperatorResponse>> operatorsIdGet(@PathVariable("id") String id) {
        return ResponseEntity.ok(Response.ok(operatorService.getOperatorById(id)));
    }

    @PutMapping("/{id}")
    public ResponseEntity<Response<OperatorResponse>> operatorsIdPut(@PathVariable("id") String id,
                                                                     @RequestBody UpdateOperatorRequest updateOperatorRequest) {
        return ResponseEntity.ok(Response.ok(operatorService.updateOperator(id, updateOperatorRequest)));
    }

    @PostMapping("/create")
    public ResponseEntity<Response<OperatorResponse>> operatorsCreatePost(@RequestBody CreateOperatorRequest createOperatorRequest) {
        return ResponseEntity.ok(Response.ok(operatorService.createOperator(createOperatorRequest)));
    }

    @PostMapping("/upload")
    public ResponseEntity<Response<OperatorResponse>> operatorsUploadPost(@RequestPart(value = "file") MultipartFile file,
                                                                          @RequestParam(value = "description") String description) {
        return ResponseEntity.ok(Response.ok(operatorService.uploadOperator(file, description)));
    }
}
