# 共享库

## 概述

共享库包含所有后端服务共用的代码和工具，包括领域构建块、异常处理、JWT 工具等。

## 架构

```
backend/shared/
├── domain-common/          # DDD 构建块、异常处理
│   └── src/main/java/com/datamate/common/
│       ├── infrastructure/exception/  # BusinessException, ErrorCode
│       ├── setting/                   # 系统参数、模型配置
│       └── domain/                    # Base entities, repositories
└── security-common/        # JWT 工具、认证辅助
    └── src/main/java/com/datamate/security/
```

## 库

### 1. domain-common

#### BusinessException
统一的业务异常处理机制：

```java
// 抛出业务异常
throw BusinessException.of(ErrorCode.DATASET_NOT_FOUND)
    .withDetail("dataset_id", datasetId);

// 带上下文的异常
throw BusinessException.of(ErrorCode.VALIDATION_FAILED)
    .withDetail("field", "email")
    .withDetail("reason", "Invalid format");
```

#### ErrorCode
错误码枚举接口：

```java
public interface ErrorCode {
    String getCode();
    String getMessage();
    HttpStatus getHttpStatus();
}

// 示例
public enum CommonErrorCode implements ErrorCode {
    SUCCESS("0000", "Success", HttpStatus.OK),
    DATABASE_NOT_FOUND("4001", "Database not found", HttpStatus.NOT_FOUND);
}
```

#### BaseEntity
所有实体的基类，包含审计字段：

```java
@Data
@EqualsAndHashCode(callSuper = true)
public class BaseEntity<T> implements Serializable {
    @TableId(type = IdType.ASSIGN_ID)
    private String id;
    
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;
    
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
    
    @TableField(fill = FieldFill.INSERT)
    private String createdBy;
    
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private String updatedBy;
}
```

### 2. security-common

#### JWT 工具
JWT Token 生成和验证：

```java
// 生成 Token
String token = JwtUtil.generateToken(userId, secret, expiration);

// 验证 Token
Claims claims = JwtUtil.validateToken(token, secret);
String userId = claims.getSubject();
```

## 使用

### 在服务中使用共享库

#### Maven 依赖
```xml
<dependency>
    <groupId>com.datamate</groupId>
    <artifactId>domain-common</artifactId>
    <version>1.0.0-SNAPSHOT</version>
</dependency>
<dependency>
    <groupId>com.datamate</groupId>
    <artifactId>security-common</artifactId>
    <version>1.0.0-SNAPSHOT</version>
</dependency>
```

#### 使用 BusinessException
```java
@RestController
@RequiredArgsConstructor
public class DatasetController {
    
    public ResponseEntity<DatasetResponse> getDataset(String id) {
        Dataset dataset = datasetService.findById(id);
        if (dataset == null) {
            throw BusinessException.of(ErrorCode.DATASET_NOT_FOUND);
        }
        return ResponseEntity.ok(DatasetResponse.from(dataset));
    }
}
```

## 快速开始

### 构建共享库
```bash
cd backend
mvn clean install
```

### 在服务中使用
共享库会自动被所有后端服务继承。

## 文档

- [AGENTS.md](./AGENTS.md)

## 相关链接

- [后端 README](../README.md)
