package com.datamate.operator.domain.repository;

import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.operator.domain.model.OperatorView;
import com.datamate.operator.interfaces.dto.OperatorDto;

import java.util.List;

public interface OperatorViewRepository extends IRepository<OperatorView> {
    List<OperatorDto> findOperatorsByCriteria(Integer page, Integer size, String keyword,
                                              List<String> categories, Boolean isStar);

    Integer countOperatorsByCriteria(String keyword, List<String> categories, Boolean isStar);

    OperatorView findOperatorById(String id);
}
