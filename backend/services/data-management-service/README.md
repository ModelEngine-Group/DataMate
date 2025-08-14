# 数据管理服务 (Data Management Service)

数据管理服务是数据引擎平台的核心组件之一，负责数据集的创建、管理和文件操作功能。

## 功能特性

- 🗂️ **数据集管理**: 创建、更新、删除和查询数据集
- 📁 **文件管理**: 上传、下载、删除数据集文件
- 🏷️ **标签系统**: 灵活的标签管理和分类
- 📊 **统计信息**: 实时的数据集统计和分析
- 🔍 **搜索功能**: 支持多条件组合搜索
- 📋 **多种数据类型**: 支持图像、文本、音频、视频、多模态数据集

## 技术栈

- **Spring Boot 3.x**: 应用框架
- **Spring Data JPA**: 数据访问层
- **MySQL 8.0**: 关系型数据库
- **Redis**: 缓存存储
- **OpenAPI 3.0**: API 规范和文档
- **Maven**: 构建工具
- **Docker**: 容器化部署

## 项目结构

```
src/
├── main/
│   ├── java/
│   │   └── com/dataengine/datamanagement/
│   │       ├── application/         # 应用服务层
│   │       │   └── service/
│   │       ├── domain/             # 领域模型层
│   │       │   ├── model/
│   │       │   └── repository/
│   │       ├── infrastructure/     # 基础设施层
│   │       │   └── config/
│   │       └── interfaces/         # 接口层
│   │           └── rest/
│   └── resources/
│       └── application.yml
└── test/
    └── java/
        └── com/dataengine/datamanagement/
```

## 环境要求

- Java 17+
- Maven 3.6+
- MySQL 8.0+
- Redis 6.0+

## 快速开始

### 1. 数据库初始化

执行初始化脚本：

```bash
mysql -u root -p < scripts/db/data-management-service-init.sql
```

### 2. 配置应用

修改 `application.yml` 中的数据库和Redis连接配置：

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/data_engine_platform
    username: your_username
    password: your_password
  redis:
    host: localhost
    port: 6379
```

### 3. 生成API代码

```bash
mvn clean compile
```

### 4. 运行应用

```bash
mvn spring-boot:run
```

## API文档

启动应用后，访问以下URL查看API文档：

- **Swagger UI**: http://localhost:8092/swagger-ui.html
- **OpenAPI JSON**: http://localhost:8092/v3/api-docs

## 主要API端点

### 数据集管理

- `GET /api/v1/data-management/datasets` - 获取数据集列表
- `POST /api/v1/data-management/datasets` - 创建数据集
- `GET /api/v1/data-management/datasets/{id}` - 获取数据集详情
- `PUT /api/v1/data-management/datasets/{id}` - 更新数据集
- `DELETE /api/v1/data-management/datasets/{id}` - 删除数据集

### 文件管理

- `GET /api/v1/data-management/datasets/{id}/files` - 获取数据集文件列表
- `POST /api/v1/data-management/datasets/{id}/files` - 上传文件
- `GET /api/v1/data-management/datasets/{id}/files/{fileId}` - 获取文件详情
- `DELETE /api/v1/data-management/datasets/{id}/files/{fileId}` - 删除文件
- `GET /api/v1/data-management/datasets/{id}/files/{fileId}/download` - 下载文件

### 标签管理

- `GET /api/v1/data-management/tags` - 获取标签列表
- `POST /api/v1/data-management/tags` - 创建标签

### 数据集类型

- `GET /api/v1/data-management/dataset-types` - 获取支持的数据集类型

## 配置说明

### 文件存储配置

```yaml
datamanagement:
  file-storage:
    upload-dir: ./uploads      # 文件上传目录
    max-file-size: 10485760    # 最大文件大小 (10MB)
    max-request-size: 52428800 # 最大请求大小 (50MB)
```

### 缓存配置

```yaml
datamanagement:
  cache:
    ttl: 3600      # 缓存TTL (秒)
    max-size: 1000 # 最大缓存条目数
```

## Docker 部署

### 构建镜像

```bash
mvn clean package
docker build -t data-management-service .
```

### 运行容器

```bash
docker run -d \
  --name data-management-service \
  -p 8092:8092 \
  -e DB_USERNAME=root \
  -e DB_PASSWORD=password \
  -e REDIS_HOST=redis \
  -v /path/to/uploads:/app/uploads \
  data-management-service
```

## 监控和健康检查

应用提供了以下监控端点：

- **健康检查**: http://localhost:8092/actuator/health
- **应用信息**: http://localhost:8092/actuator/info
- **指标数据**: http://localhost:8092/actuator/metrics

## 开发指南

### 添加新的数据集类型

1. 在 `DatasetTypeController` 中添加新的类型定义
2. 更新相关的验证逻辑
3. 如需要，更新数据库架构

### 扩展文件处理

1. 在 `DatasetFileApplicationService` 中添加新的文件处理逻辑
2. 考虑添加文件格式验证
3. 更新相关的业务规则

## 测试

运行单元测试：

```bash
mvn test
```

运行集成测试：

```bash
mvn verify
```

## 故障排除

### 常见问题

1. **文件上传失败**
   - 检查文件大小是否超过限制
   - 确认上传目录权限正确
   - 查看应用日志获取详细错误信息

2. **数据库连接问题**
   - 验证数据库连接配置
   - 确认数据库服务正常运行
   - 检查网络连接

3. **API生成失败**
   - 确认OpenAPI规范文件存在
   - 检查Maven插件配置
   - 清理并重新构建项目

### 日志位置

- **应用日志**: `logs/data-management-service.log`
- **控制台输出**: 标准输出

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](../../../LICENSE) 文件了解详情。
