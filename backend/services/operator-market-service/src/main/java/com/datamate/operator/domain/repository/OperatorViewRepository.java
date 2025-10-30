package com.datamate.operator.domain.repository;

import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.operator.domain.model.OperatorView;

import java.util.List;

public interface OperatorViewRepository extends IRepository<OperatorView> {
    List<OperatorView> findOperatorsByCriteria(Integer page, Integer size, String operatorName,
                                               List<String> categories, Boolean isStar);

    Integer countOperatorsByCriteria(String operatorName, List<String> categories, Boolean isStar);

    OperatorView findOperatorById(String id);
}
