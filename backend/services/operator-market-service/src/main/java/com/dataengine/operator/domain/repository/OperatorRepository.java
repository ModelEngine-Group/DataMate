package com.dataengine.operator.domain.repository;

import com.dataengine.operator.domain.modal.OperatorEntity;
import org.springframework.data.jpa.repository.JpaRepository;

public interface OperatorRepository extends JpaRepository<OperatorEntity, Long> {
}

