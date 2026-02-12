package com.datamate.common.infrastructure.config;

import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import org.apache.ibatis.type.JdbcType;
import org.apache.ibatis.type.MappedJdbcTypes;
import org.apache.ibatis.type.MappedTypes;
import org.postgresql.util.PGobject;

import java.lang.reflect.Field;
import java.sql.PreparedStatement;
import java.sql.SQLException;

// 指定处理的 Java 类型和 JDBC 类型
@MappedTypes({Object.class})
@MappedJdbcTypes(JdbcType.OTHER)
public class PgJsonTypeHandler extends JacksonTypeHandler {

    public PgJsonTypeHandler(Class<?> type) {
        super(type);
    }

    public PgJsonTypeHandler(Class<?> type, Field field) {
        super(type, field);
    }

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, Object parameter, JdbcType jdbcType) throws SQLException {
        // 1. 先借助父类转成 JSON 字符串
        String json = this.toJson(parameter);

        // 2. 核心：封装成 PGobject，并指定类型为 'json' 或 'jsonb'
        PGobject jsonObject = new PGobject();
        // 如果你的数据库字段是 jsonb，这里一定要写 "jsonb"；如果是 json，写 "json"
        jsonObject.setType("json");
        jsonObject.setValue(json);

        // 3. 传给驱动
        ps.setObject(i, jsonObject);
    }
}