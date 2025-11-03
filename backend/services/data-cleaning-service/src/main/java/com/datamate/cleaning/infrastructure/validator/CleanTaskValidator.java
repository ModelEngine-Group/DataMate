package com.datamate.cleaning.infrastructure.validator;

import com.datamate.cleaning.common.exception.CleanErrorCode;
import com.datamate.cleaning.domain.repository.CleaningTaskRepository;
import com.datamate.cleaning.interfaces.dto.OperatorInstanceDto;
import com.datamate.common.infrastructure.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Locale;


@Component
@RequiredArgsConstructor
public class CleanTaskValidator {
    private final CleaningTaskRepository cleaningTaskRepo;

    public void checkNameDuplication (String name) {
        if (cleaningTaskRepo.isNameExist(name)) {
            throw BusinessException.of(CleanErrorCode.DUPLICATE_TASK_NAME);
        }
    }

    public void checkInputAndOutput (List<OperatorInstanceDto> operators) {
        if (operators == null || operators.size() <= 1) {
            return;
        }
        for (int i = 1; i < operators.size(); i++) {
            OperatorInstanceDto front = operators.get(i - 1);
            OperatorInstanceDto back = operators.get(i);
            if (!StringUtils.equals(front.getOutputs(), back.getInputs())) {
                throw BusinessException.of(CleanErrorCode.IN_AND_OUT_NOT_MATCH,
                    String.format(Locale.ROOT, "ops(name: [%s, %s]) inputs and outputs does not match",
                        front.getName(), back.getName()));
            }
        }
    }
}
