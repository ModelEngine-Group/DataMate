package com.dataengine.operator.application;

import com.dataengine.operator.infrastructure.persistence.mapper.OperatorMapper;
import com.dataengine.operator.interfaces.dto.*;
import com.dataengine.operator.domain.modal.OperatorEntity;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class OperatorService {
    private final OperatorMapper operatorMapper;

    public List<OperatorResponse> getOperators(Integer page, Integer size, List<Integer> categories,
                                              String operatorName, String labelName) {
        return new ArrayList<>();
    }

    private OperatorResponse toDto(OperatorEntity entity) {
        OperatorResponse dto = new OperatorResponse();
        dto.setId(entity.getId());
        dto.setName(entity.getName());
        dto.setDescription(entity.getDescription());
        dto.setVersion(entity.getVersion());
        return dto;
    }
    public OperatorResponse getOperatorById(String id) {
        // TODO: 查询算子详情
        return new OperatorResponse();
    }
    public OperatorResponse updateOperator(String id, UpdateOperatorRequest req) {
        // TODO: 更新算子
        return new OperatorResponse();
    }
    public OperatorResponse createOperator(CreateOperatorRequest req) {
        // TODO: 创建算子
        return new OperatorResponse();
    }
    public OperatorResponse uploadOperator(MultipartFile file, String description) {
        // TODO: 文件上传与解析
        return new OperatorResponse();
    }
}
