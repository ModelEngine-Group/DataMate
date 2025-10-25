package com.datamate.operator.application;

import com.datamate.operator.infrastructure.converter.OperatorConverter;
import com.datamate.operator.domain.model.OperatorView;
import com.datamate.operator.domain.repository.CategoryRelationRepository;
import com.datamate.operator.domain.repository.OperatorRepository;
import com.datamate.operator.domain.repository.OperatorViewRepository;
import com.datamate.operator.interfaces.dto.OperatorDto;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@Service
@RequiredArgsConstructor
public class OperatorService {
    private final OperatorRepository operatorRepo;

    private final OperatorViewRepository operatorViewRepo;

    private final CategoryRelationRepository relationRepo;

    public List<OperatorDto> getOperators(Integer page, Integer size, List<Integer> categories,
                                          String operatorName, Boolean isStar) {
        List<OperatorView> filteredOperators = operatorViewRepo.findOperatorsByCriteria(page, size, operatorName,
                categories, isStar);
        return filteredOperators.stream().map(OperatorConverter.INSTANCE::fromEntityToDto).toList();
    }

    public int getOperatorsCount(List<Integer> categories, String operatorName, Boolean isStar) {
        return operatorViewRepo.countOperatorsByCriteria(operatorName, categories, isStar);
    }

    public OperatorDto getOperatorById(String id) {
        OperatorView operator = operatorViewRepo.findOperatorById(id);
        return OperatorConverter.INSTANCE.fromEntityToDto(operator);
    }

    public OperatorDto createOperator(OperatorDto req) {
        operatorRepo.insertOperator(req);
        relationRepo.batchInsert(req.getId(), req.getCategories());
        return getOperatorById(req.getId());
    }

    public OperatorDto updateOperator(String id, OperatorDto req) {
        operatorRepo.updateOperator(req);
        relationRepo.batchInsert(id, req.getCategories());
        return getOperatorById(id);
    }

    public OperatorDto uploadOperator(MultipartFile file, String description) {
        // TODO: 文件上传与解析
        return new OperatorDto();
    }
}
