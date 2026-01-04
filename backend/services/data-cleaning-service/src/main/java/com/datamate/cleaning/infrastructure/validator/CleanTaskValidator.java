package com.datamate.cleaning.infrastructure.validator;

import com.datamate.cleaning.common.enums.ExecutorType;
import com.datamate.cleaning.common.exception.CleanErrorCode;
import com.datamate.cleaning.domain.repository.CleaningTaskRepository;
import com.datamate.cleaning.interfaces.dto.OperatorInstanceDto;
import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.datamate.common.setting.application.SysParamApplicationService;
import com.datamate.operator.domain.contants.OperatorConstant;
import lombok.RequiredArgsConstructor;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Locale;
import java.util.regex.Pattern;


@Component
@RequiredArgsConstructor
public class CleanTaskValidator {
    private final CleaningTaskRepository cleaningTaskRepo;

    private final SysParamApplicationService sysParamApplicationService;

    private final Pattern UUID_PATTERN = Pattern.compile(
            "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    );

    public void checkNameDuplication(String name) {
        if (cleaningTaskRepo.isNameExist(name)) {
            throw BusinessException.of(CleanErrorCode.DUPLICATE_TASK_NAME);
        }
    }

    public void checkInputAndOutput(List<OperatorInstanceDto> operators) {
        if (operators == null || operators.size() <= 1) {
            return;
        }
        for (int i = 1; i < operators.size(); i++) {
            OperatorInstanceDto front = operators.get(i - 1);
            OperatorInstanceDto back = operators.get(i);
            if (StringUtils.equals(front.getOutputs(), back.getInputs()) || StringUtils.equalsAny("multimodal",
                    front.getOutputs(), back.getOutputs())) {
                continue;
            }
            throw BusinessException.of(CleanErrorCode.IN_AND_OUT_NOT_MATCH,
                    String.format(Locale.ROOT, "ops(name: [%s, %s]) inputs and outputs does not match",
                            front.getName(), back.getName()));
        }
    }

    public void checkTaskId(String id) {
        if (id == null || !UUID_PATTERN.matcher(id).matches()) {
            throw BusinessException.of(SystemErrorCode.INVALID_PARAMETER);
        }
    }

    public ExecutorType checkAndGetExecutorType(List<OperatorInstanceDto> operators) {
        if (operators == null || operators.isEmpty()) {
            throw BusinessException.of(CleanErrorCode.OPERATOR_LIST_EMPTY);
        }
        for (int i = 1; i < operators.size(); i++) {
            OperatorInstanceDto front = operators.get(i - 1);
            OperatorInstanceDto back = operators.get(i);
            boolean frontHas = CollectionUtils.isNotEmpty(front.getCategories())
                    && front.getCategories().contains(OperatorConstant.CATEGORY_DATA_JUICER_ID);
            boolean backHas = CollectionUtils.isNotEmpty(back.getCategories())
                    && back.getCategories().contains(OperatorConstant.CATEGORY_DATA_JUICER_ID);
            if (frontHas == backHas) {
                continue;
            }
            throw BusinessException.of(CleanErrorCode.EXECUTOR_NOT_MATCH,
                    String.format(Locale.ROOT, "ops(name: [%s, %s]) executor does not match",
                            front.getName(), back.getName()));
        }
        if (operators.getFirst().getCategories().contains(OperatorConstant.CATEGORY_DATA_JUICER_ID)) {
            return ExecutorType.fromValue(sysParamApplicationService.getParamByKey("DATA_JUICER_EXECUTOR"));
        }
        return ExecutorType.DATAMATE;
    }
}
