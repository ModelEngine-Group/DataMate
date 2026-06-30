package com.datamate.common.infrastructure.config;

import com.baomidou.mybatisplus.core.handlers.MetaObjectHandler;
import lombok.extern.slf4j.Slf4j;
import org.apache.ibatis.reflection.MetaObject;
import org.springframework.context.annotation.Configuration;

import java.time.LocalDateTime;

/**
 * 持久化实体元数据对象处理器
 *
 * @author dallas
 * @since 2025-10-17
 */
@Slf4j
@Configuration
public class EntityMetaObjectHandler implements MetaObjectHandler {
    @Override
    public void insertFill(MetaObject metaObject) {
        log.debug("Starting insert fill...");

        // 创建时间填充
        this.strictInsertFill(metaObject, "createdAt", LocalDateTime.class, LocalDateTime.now());
        // 更新时间填充
        this.strictInsertFill(metaObject, "updatedAt", LocalDateTime.class, LocalDateTime.now());
        // 创建人填充（需要从安全上下文获取当前用户）
        String currentUser = getCurrentUser();
        this.strictInsertFill(metaObject, "createdBy", String.class, currentUser);
        // 更新人填充
        this.strictInsertFill(metaObject, "updatedBy", String.class, currentUser);
    }

    @Override
    public void updateFill(MetaObject metaObject) {
        log.debug("Starting update fill...");
        // 更新时间填充
        this.strictUpdateFill(metaObject, "updatedAt", LocalDateTime.class, LocalDateTime.now());
        // 更新人填充
        this.strictUpdateFill(metaObject, "updatedBy", String.class, getCurrentUser());
    }

    /**
     * 获取当前用户（需要根据你的安全框架实现）
     */
    private String getCurrentUser() {
        // todo 这里需要根据你的安全框架实现，例如Spring Security、Shiro等
        // 示例：返回默认用户或从SecurityContext获取
        try {
            // 如果是Spring Security
            // return SecurityContextHolder.getContext().getAuthentication().getName();

            // 临时返回默认值，请根据实际情况修改
            return "system";
        } catch (Exception e) {
            log.error("Error getting current user", e);
            return "unknown";
        }
    }
}
