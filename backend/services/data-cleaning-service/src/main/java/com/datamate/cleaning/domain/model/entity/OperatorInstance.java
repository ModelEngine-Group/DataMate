package com.datamate.cleaning.domain.model.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@TableName(value = "t_operator_instance", autoResultMap = true)
public class OperatorInstance {
    private String instanceId;

    private String operatorId;

    private int opIndex;

    private String settingsOverride;
}
