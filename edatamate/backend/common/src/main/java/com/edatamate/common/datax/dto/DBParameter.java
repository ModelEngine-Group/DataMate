package com.edatamate.common.datax.dto;


import lombok.Getter;
import lombok.Setter;

import java.util.List;
import java.util.Map;

@Getter
@Setter
public class DBParameter extends Parameter {
    private List<Map<String, Object>> connection;

    private List<String> column;

    private String jdbcUrl;

    private String table;

    private String username;

    private String password;

    private String querySql;
}
