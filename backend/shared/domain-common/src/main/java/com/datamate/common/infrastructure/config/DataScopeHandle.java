package com.datamate.common.infrastructure.config;

import com.baomidou.mybatisplus.extension.plugins.handler.DataPermissionHandler;
import com.datamate.common.domain.model.base.BaseEntity;
import lombok.extern.slf4j.Slf4j;
import net.sf.jsqlparser.expression.Expression;
import net.sf.jsqlparser.expression.StringValue;
import net.sf.jsqlparser.expression.operators.conditional.AndExpression;
import net.sf.jsqlparser.expression.operators.relational.InExpression;
import net.sf.jsqlparser.expression.operators.relational.ParenthesedExpressionList;
import net.sf.jsqlparser.schema.Column;
import org.apache.commons.lang3.ObjectUtils;
import org.apache.commons.lang3.StringUtils;
import org.apache.ibatis.executor.Executor;
import org.apache.ibatis.mapping.MappedStatement;
import org.apache.ibatis.mapping.SqlCommandType;
import org.apache.ibatis.plugin.Interceptor;
import org.apache.ibatis.plugin.Intercepts;
import org.apache.ibatis.plugin.Invocation;
import org.apache.ibatis.plugin.Signature;
import org.springframework.stereotype.Component;

import java.lang.reflect.Method;
import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.Objects;

/**
 * 数据隔离处理
 *
 * @since 2026/1/19
 */
@Slf4j
@Component
@Intercepts({
        @Signature(type = Executor.class, method = "update",
                args = {MappedStatement.class, Object.class})
})
public class DataScopeHandle implements DataPermissionHandler, Interceptor {
    private static final ThreadLocal<String> userInfoHolder = new ThreadLocal<>();

    private static final StringValue SYSTEM_USER = new StringValue("system");

    private static final String FILTER_COLUMN_NAME = "created_by";

    private static final String C_DOTS = ".";

    public static void setUserInfo(String user) {
        userInfoHolder.set(user);
    }

    public static void removeUserInfo() {
        userInfoHolder.remove();
    }

    @Override
    public Expression getSqlSegment(Expression where, String mappedStatementId) {
        if (StringUtils.isBlank(userInfoHolder.get())) {
            return where;
        }
        try {
            String className = mappedStatementId.substring(0, mappedStatementId.lastIndexOf(C_DOTS));
            Class<?> clazz = Class.forName(className);
            IgnoreDataScopeAnnotation annotation = clazz.getAnnotation(IgnoreDataScopeAnnotation.class);
            if (annotation != null) {
                return where;
            }
            String methodName = mappedStatementId.substring(mappedStatementId.lastIndexOf(C_DOTS) + 1);
            for (Method method : clazz.getMethods()) {
                if (method.getName().equals(methodName)) {
                    annotation = method.getAnnotation(IgnoreDataScopeAnnotation.class);
                    if (annotation != null) {
                        return where;
                    }
                    break;
                }
            }
            ParenthesedExpressionList<StringValue> valueList =
                    new ParenthesedExpressionList<>(Arrays.asList(new StringValue(userInfoHolder.get()), SYSTEM_USER));
            InExpression inExpression = new InExpression();
            inExpression.setLeftExpression(new Column(FILTER_COLUMN_NAME));
            inExpression.setRightExpression(valueList);
            return ObjectUtils.isNotEmpty(where) ? new AndExpression(where, inExpression) : inExpression;
        } catch (Exception e) {
            log.warn(e.getMessage());
        }
        return where;
    }

    @Override
    public Object intercept(Invocation invocation) throws Throwable {
        MappedStatement ms = (MappedStatement) invocation.getArgs()[0];
        Object parameter = invocation.getArgs()[1];

        if (parameter instanceof BaseEntity baseEntity) {
            // 根据SQL命令类型设置审计字段
            log.info("current user {}, ms {}", userInfoHolder.get(), ms);
            if (Objects.requireNonNull(ms.getSqlCommandType()) != SqlCommandType.UPDATE) {
                baseEntity.setCreatedAt(LocalDateTime.now());
                baseEntity.setCreatedBy(userInfoHolder.get());
            }
            baseEntity.setUpdatedAt(LocalDateTime.now());
            baseEntity.setUpdatedBy(userInfoHolder.get());
        }
        return invocation.proceed();
    }
}
