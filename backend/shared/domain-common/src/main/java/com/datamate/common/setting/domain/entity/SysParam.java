package com.datamate.common.setting.domain.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import com.datamate.common.domain.model.base.BaseEntity;
import lombok.Getter;
import lombok.Setter;

/**
 * 系统参数设置实体类
 *
 * @author dallas
 * @since 2025-10-27
 */
@Setter
@Getter
@TableName("t_sys_param")
public class SysParam extends BaseEntity<String> {
    /**
     * 设置项值
     */
    private String paramValue;

    /**
     * 设置项类型（如 string、integer、boolean）
     */
    private String paramType;

    /**
     * 选项列表（JSON格式，仅对enum类型有效）
     */
    private String optionList;

    /**
     * 设置项描述
     */
    private String description;

    /**
     * 是否内置：1-是，0-否
     */
    private Boolean isBuiltIn;

    /**
     * 是否可修改：1-可修改，0-不可修改
     */
    private Boolean canModify;

    /**
     * 是否启用：1-启用，0-禁用
     */
    private Boolean isEnabled;
}
