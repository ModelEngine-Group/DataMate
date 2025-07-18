package com.edatamate.common.datax.dto;

import lombok.Getter;

@Getter
public enum JobEnum {
    NAS("nas", NasParameter.class),
    OBS("obs", ObsParameter.class),
    MYSQL("mysql", MysqlParameter.class),
    PGSQL("postgresql", PgsqlParameter.class);

    private final String type;

    private final Class<? extends Parameter> parameter;

    JobEnum(String type, Class<? extends Parameter> parameter) {
        this.type = type;
        this.parameter = parameter;
    }

    public static JobEnum of(String type) {
        for (JobEnum e : values()) {
            if (e.getType().equalsIgnoreCase(type)) {
                return e;
            }
        }
        throw new IllegalArgumentException();
    }
}
