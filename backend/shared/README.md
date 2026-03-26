# Shared Libraries

## Overview

Shared Libraries contain code and utilities shared across all backend services, including domain building blocks, exception handling, JWT utilities, and more.

## Architecture

```
backend/shared/
├── domain-common/          # DDD building blocks, exception handling
│   └── src/main/java/com/datamate/common/
│       ├── infrastructure/exception/  # BusinessException, ErrorCode
│       ├── setting/                   # System params, model configs
│       └── domain/                    # Base entities, repositories
└── security-common/        # JWT utilities, auth helpers
    └── src/main/java/com/datamate/security/
```

## Libraries

### 1. domain-common

#### BusinessException
Unified business exception handling mechanism:

```java
// Throw business exception
throw BusinessException.of(ErrorCode.DATASET_NOT_FOUND)
    .withDetail("dataset_id", datasetId);

// Exception with context
throw BusinessException.of(ErrorCode.VALIDATION_FAILED)
    .withDetail("field", "email")
    .withDetail("reason", "Invalid format");
```

#### ErrorCode
Error code enumeration interface:

```java
public interface ErrorCode {
    String getCode();
    String getMessage();
    HttpStatus getHttpStatus();
}

// Example
public enum CommonErrorCode implements ErrorCode {
    SUCCESS("0000", "Success", HttpStatus.OK),
    DATABASE_NOT_FOUND("4001", "Database not found", HttpStatus.NOT_FOUND);
}
```

#### BaseEntity
Base class for all entities, including audit fields:

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

#### JWT Utilities
JWT Token generation and validation:

```java
// Generate Token
String token = JwtUtil.generateToken(userId, secret, expiration);

// Validate Token
Claims claims = JwtUtil.validateToken(token, secret);
String userId = claims.getSubject();
```

## Usage

### Using Shared Libraries in Services

#### Maven Dependencies
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

#### Using BusinessException
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

## Quick Start

### Build Shared Libraries
```bash
cd backend
mvn clean install
```

### Use in Services
Shared libraries are automatically inherited by all backend services.

## Documentation

- [AGENTS.md](./AGENTS.md)

## Related Links

- [Backend README](../README.md)
