package com.datamate.operator.domain.repository;

import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.operator.domain.model.Operator;
import com.datamate.operator.interfaces.dto.OperatorDto;

import java.util.List;

public interface OperatorRepository extends IRepository<Operator> {
    List<OperatorDto> findAllOperators();

    void updateOperator(OperatorDto operator);

    void insertOperator(OperatorDto operator);

    void deleteOperator(String id);

    int countOperatorByStar(boolean isStar);

    boolean operatorInTemplateOrRunning(String operatorId);

    void incrementUsageCount(List<String> operatorIds);
}
