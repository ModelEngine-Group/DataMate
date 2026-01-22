package com.datamate.operator.domain.repository;

import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.operator.domain.model.OperatorRelease;
import com.datamate.operator.interfaces.dto.OperatorReleaseDto;

import java.util.List;

public interface OperatorReleaseRepository extends IRepository<OperatorRelease> {
    List<OperatorReleaseDto> findAllByOperatorId(String operatorId);

    void insertOperatorRelease(OperatorReleaseDto operatorRelease);

    void updateOperatorRelease(OperatorReleaseDto operatorRelease);

    void deleteOperatorRelease(String operatorId);
}
