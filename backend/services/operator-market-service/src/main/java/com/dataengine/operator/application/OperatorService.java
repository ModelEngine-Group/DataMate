package com.dataengine.operator.application;

import com.dataengine.operator.interfaces.dto.*;
import com.dataengine.operator.domain.modal.OperatorEntity;
import com.dataengine.operator.domain.repository.OperatorRepository;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Example;
import org.springframework.data.domain.ExampleMatcher;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class OperatorService {
    @Autowired
    private OperatorRepository operatorRepository;

    public PagedOperatorResponse getOperators(Integer page, Integer size, List<Integer> categories,
                                              String operatorName, String labelName) {
        return new PagedOperatorResponse();
    }

    private OperatorResponse toDto(OperatorEntity entity) {
        OperatorResponse dto = new OperatorResponse();
        dto.setId(entity.getId());
        dto.setName(entity.getName());
        dto.setDescription(entity.getDescription());
        dto.setCategory(entity.getCategory());
        dto.setVersion(entity.getVersion());
        dto.setAuthor(entity.getAuthor());
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
