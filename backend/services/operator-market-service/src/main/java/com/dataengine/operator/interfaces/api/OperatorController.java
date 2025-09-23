package com.dataengine.operator.interfaces.api;

import com.dataengine.operator.domain.converter.OperatorConverter;
import com.dataengine.operator.domain.modal.Operator;
import com.dataengine.operator.infrastructure.persistence.mapper.OperatorMapper;
import com.dataengine.operator.interfaces.dto.*;
import com.dataengine.operator.application.OperatorService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
@RequiredArgsConstructor
public class OperatorController implements OperatorApi {
    private final OperatorService operatorService;

    private final OperatorMapper operatorMapper;

    @Override
    public ResponseEntity<List<OperatorResponse>> operatorsListPost(OperatorsListPostRequest request) {
        List<Operator> allOperators = operatorMapper.findAllOperators();
        List<OperatorResponse> responses = allOperators.stream()
            .map(OperatorConverter.INSTANCE::operatorToResponse).toList();
        return ResponseEntity.ok(responses);
    }

    @Override
    public ResponseEntity<OperatorResponse> operatorsIdGet(String id) {
        return ResponseEntity.ok(operatorService.getOperatorById(id));
    }

    @Override
    public ResponseEntity<OperatorResponse> operatorsIdPut(String id, UpdateOperatorRequest updateOperatorRequest) {
        return ResponseEntity.ok(operatorService.updateOperator(id, updateOperatorRequest));
    }

    @Override
    public ResponseEntity<OperatorResponse> operatorsCreatePost(CreateOperatorRequest createOperatorRequest) {
        return ResponseEntity.ok(operatorService.createOperator(createOperatorRequest));
    }

    @Override
    public ResponseEntity<OperatorResponse> operatorsUploadPost(MultipartFile file, String description) {
        return ResponseEntity.ok(operatorService.uploadOperator(file, description));
    }
}

