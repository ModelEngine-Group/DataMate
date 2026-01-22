package com.datamate.operator.domain.model;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.datamate.common.infrastructure.config.PgJsonTypeHandler;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.List;

@Getter
@Setter
@TableName(value = "t_operator_release", autoResultMap = true)
public class OperatorRelease {
    private String id;

    private String version;

    private LocalDateTime releaseDate;

    @TableField(typeHandler = PgJsonTypeHandler.class)
    private List<String> changelog;
}
