package com.edatamate.common.datax.dto;


import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Builder
@Getter
@Setter
public class MysqlParameter extends DBParameter {
    private String where;

    private List<String> preSql;

    private List<String> postSql;

    private List<String> session;

    private String writeMode;

    private String querySql;

    private String splitPk;

    private int batchSize;
}
