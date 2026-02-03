"""
核心异常处理模块

为应用程序提供统一、优雅的异常处理系统，确保所有 API 响应都符合标准化格式。

## 快速开始

### 1. 注册异常处理器（在 main.py 中）

```python
from app.core.exception import register_exception_handlers, ExceptionHandlingMiddleware

app = FastAPI()

# 注册全局异常捕获中间件（最外层）
app.add_middleware(ExceptionHandlingMiddleware)

# 注册异常处理器
register_exception_handlers(app)
```

### 2. 在代码中抛出业务异常

```python
from app.core.exception import ErrorCodes, BusinessError

# 资源不存在
async def get_user(user_id: str):
    user = await db.get_user(user_id)
    if not user:
        raise BusinessError(ErrorCodes.NOT_FOUND)
    return user

# 参数验证失败
async def create_user(name: str):
    if not name:
        raise BusinessError(ErrorCodes.BAD_REQUEST)
    # ...
```

### 3. 返回成功响应

```python
from app.core.exception import SuccessResponse

@router.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await service.get_user(user_id)
    return SuccessResponse(data=user)
    # 返回格式: {"code": "0", "message": "success", "data": {...}}
```

### 4. 使用事务管理

```python
from app.core.exception import transaction, BusinessError, ErrorCodes

@router.post("/users")
async def create_user(request: CreateUserRequest, db: AsyncSession = Depends(get_db)):
    async with transaction(db):
        # 所有数据库操作
        user = User(name=request.name)
        db.add(user)
        await db.flush()

        # 如果抛出异常，事务会自动回滚
        if check_duplicate(user.name):
            raise BusinessError(ErrorCodes.OPERATION_FAILED)

    # 事务已自动提交
    return SuccessResponse(data=user)
```

## 异常类型说明

### BusinessError（业务异常）
用于预期的业务错误，如资源不存在、权限不足、参数错误等。

特点：
- 不会记录完整的堆栈跟踪（因为这是预期内的错误）
- 返回对应的 HTTP 状态码（400、404 等）
- 客户端会收到标准化的错误响应

使用场景：
- 资源不存在
- 参数验证失败
- 权限不足
- 业务规则违反

### SystemError（系统异常）
用于意外的系统错误，如数据库错误、网络错误、配置错误等。

特点：
- 记录完整的堆栈跟踪
- 返回 HTTP 500
- 不暴露敏感的系统信息给客户端

使用场景：
- 数据库连接失败
- 网络超时
- 配置错误
- 编程错误

## 错误码定义

所有错误码在 `ErrorCodes` 类中集中定义，遵循规范：`{module}.{sequence}`

### 通用错误码
- `SUCCESS` (0): 操作成功
- `BAD_REQUEST` (common.0001): 请求参数错误
- `NOT_FOUND` (common.0002): 资源不存在
- `FORBIDDEN` (common.0003): 权限不足
- `UNAUTHORIZED` (common.0004): 未授权访问
- `VALIDATION_ERROR` (common.0005): 数据验证失败

### 系统级错误码
- `INTERNAL_ERROR` (system.0001): 服务器内部错误
- `DATABASE_ERROR` (system.0002): 数据库错误
- `NETWORK_ERROR` (system.0003): 网络错误

### 模块错误码
- `annotation.*`: 标注模块相关错误
- `collection.*`: 归集模块相关错误
- `evaluation.*`: 评估模块相关错误
- `generation.*`: 生成模块相关错误
- `rag.*`: RAG 模块相关错误
- `ratio.*`: 配比模块相关错误

## Result 类型（可选的函数式错误处理）

如果你不喜欢使用异常，可以使用 Result 类型进行函数式错误处理：

```python
from app.core.exception import Result, Ok, Err, ErrorCodes

def get_user(user_id: str) -> Result[User]:
    user = db.find_user(user_id)
    if user:
        return Ok(user)
    return Err(ErrorCodes.NOT_FOUND)

# 使用结果
result = get_user("123")
if result.is_ok():
    user = result.unwrap()
    print(f"User: {user.name}")
else:
    error = result.unwrap_err()
    print(f"Error: {error.message}")

# 链式操作
result = get_user("123")
    .map(lambda user: user.name)
    .and_then(validate_name)
```

## 响应格式

### 成功响应
```json
{
  "code": "0",
  "message": "success",
  "data": {
    "id": 123,
    "name": "张三"
  }
}
```

### 错误响应
```json
{
  "code": "common.0002",
  "message": "资源不存在",
  "data": null
}
```

## 最佳实践

1. **始终使用业务异常**：对于可预见的业务错误，使用 `BusinessError` 而不是 HTTPException
2. **集中定义错误码**：所有错误码在 `ErrorCodes` 中定义，不要硬编码
3. **提供有用的数据**：在抛出异常时，可以通过 `data` 参数传递额外的错误信息
4. **使用事务管理**：涉及多个数据库操作时，使用 `transaction` 上下文管理器
5. **不要捕获 SystemError**：让系统错误由全局处理器统一处理

## 迁移指南

如果你有旧的异常处理代码，迁移步骤：

1. 删除旧的异常类定义
2. 将 `raise OldException(...)` 替换为 `raise BusinessError(ErrorCodes.XXX)`
3. 移除 try-except 中的异常转换逻辑，让全局处理器处理
4. 更新导入语句：`from app.core.exception import ErrorCodes, BusinessError`

## 测试

可以使用测试端点验证异常处理：

```bash
curl http://localhost:8000/test-success
curl http://localhost:8000/test-business-error
curl http://localhost:8000/test-system-error
```
"""

from .base import BaseError, ErrorCode, SystemError, BusinessError
from .codes import ErrorCodes
from .handlers import (
    register_exception_handlers,
    ErrorResponse,
    SuccessResponse
)
from .middleware import ExceptionHandlingMiddleware
from .result import Result, Ok, Err
from .transaction import transaction, ensure_transaction_rollback

__all__ = [
    # 基础异常类
    'BaseError',
    'ErrorCode',
    'SystemError',
    'BusinessError',
    # 错误码
    'ErrorCodes',
    # 处理器
    'register_exception_handlers',
    'ErrorResponse',
    'SuccessResponse',
    # 中间件
    'ExceptionHandlingMiddleware',
    # Result 类型
    'Result',
    'Ok',
    'Err',
    # 事务管理
    'transaction',
    'ensure_transaction_rollback',
]
