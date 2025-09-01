# 数据归集服务 (Data Collection Service)

基于DataX的数据归集和同步服务，提供多数据源之间的数据同步功能。

## 功能特性

- 🔗 **多数据源支持**: 支持MySQL、PostgreSQL、Oracle、SQL Server等主流数据库
- 📊 **任务管理**: 创建、配置、执行和监控数据同步任务
- ⏰ **定时调度**: 支持Cron表达式的定时任务
- 📈 **实时监控**: 任务执行进度、状态和性能指标监控
- 📝 **执行日志**: 详细的任务执行日志记录
- 🔌 **插件化**: DataX Reader/Writer插件化集成

## 技术架构

- **框架**: Spring Boot 3.x
- **数据库**: MySQL + MyBatis
- **同步引擎**: DataX
- **API**: OpenAPI 3.0 自动生成
- **架构模式**: DDD (领域驱动设计)

## 项目结构

```
src/main/java/com/dataengine/collection/
├── DataCollectionApplication.java          # 应用启动类
├── domain/                                  # 领域层
│   ├── model/                              # 领域模型
│   │   ├── DataSource.java                 # 数据源实体
│   │   ├── CollectionTask.java             # 归集任务实体
│   │   ├── TaskExecution.java              # 任务执行记录
│   │   └── ExecutionLog.java               # 执行日志
│   └── service/                            # 领域服务
│       ├── DataSourceService.java
│       ├── CollectionTaskService.java
│       ├── TaskExecutionService.java
│       └── impl/                           # 服务实现
├── infrastructure/                          # 基础设施层
│   ├── config/                             # 配置类
│   ├── datax/                              # DataX执行引擎
│   │   └── DataXExecutionEngine.java
│   └── persistence/                        # 持久化
│       ├── mapper/                         # MyBatis Mapper
│       └── typehandler/                    # 类型处理器
└── interfaces/                             # 接口层
    ├── api/                                # OpenAPI生成的接口
    ├── dto/                                # OpenAPI生成的DTO
    └── rest/                               # REST控制器
        ├── DataSourceController.java
        ├── CollectionTaskController.java
        ├── TaskExecutionController.java
        └── exception/                      # 异常处理

src/main/resources/
├── mappers/                                # MyBatis XML映射文件
├── application.properties                  # 应用配置
└── ...
```

## 环境要求

- Java 17+
- Maven 3.6+
- MySQL 8.0+
- DataX 3.0+
- Redis (可选，用于缓存)

## 配置说明

### 应用配置 (application.properties)

```properties
# 服务端口
server.port=8090

# 数据库配置
spring.datasource.url=jdbc:mysql://localhost:3306/knowledge_base
spring.datasource.username=root
spring.datasource.password=123456

# DataX配置
datax.home=/runtime/datax
datax.python.path=/runtime/datax/bin/datax.py
datax.job.timeout=7200
datax.job.memory=2g
```

### DataX配置

确保DataX已正确安装并配置：

1. 下载DataX到 `/runtime/datax` 目录
2. 配置相关Reader/Writer插件
3. 确保Python环境可用

## 数据库初始化

执行数据库初始化脚本：

```bash
mysql -u root -p knowledge_base < scripts/db/data-collection-init.sql
```

## 构建和运行

### 1. 编译项目

```bash
cd backend/services/data-collection-service
mvn clean compile
```

这将触发OpenAPI代码生成。

### 2. 打包

```bash
mvn clean package -DskipTests
```

### 3. 运行

作为独立服务运行：
```bash
java -jar target/data-collection-service-1.0.0-SNAPSHOT.jar
```

或通过main-application统一启动：
```bash
cd backend/services/main-application
mvn spring-boot:run
```

## API文档

服务启动后，可通过以下地址访问API文档：

- Swagger UI: http://localhost:8090/swagger-ui.html
- OpenAPI JSON: http://localhost:8090/v3/api-docs

## 主要API端点

### 数据源管理

- `GET /api/v1/collection/datasources` - 获取数据源列表
- `POST /api/v1/collection/datasources` - 创建数据源
- `GET /api/v1/collection/datasources/{id}` - 获取数据源详情
- `PUT /api/v1/collection/datasources/{id}` - 更新数据源
- `DELETE /api/v1/collection/datasources/{id}` - 删除数据源
- `POST /api/v1/collection/datasources/{id}/test` - 测试连接

### 归集任务管理

- `GET /api/v1/collection/tasks` - 获取任务列表
- `POST /api/v1/collection/tasks` - 创建任务
- `GET /api/v1/collection/tasks/{id}` - 获取任务详情
- `PUT /api/v1/collection/tasks/{id}` - 更新任务
- `DELETE /api/v1/collection/tasks/{id}` - 删除任务

### 任务执行管理

- `POST /api/v1/collection/tasks/{id}/execute` - 执行任务
- `POST /api/v1/collection/tasks/{id}/stop` - 停止任务
- `GET /api/v1/collection/executions` - 获取执行历史
- `GET /api/v1/collection/executions/{executionId}` - 获取执行详情
- `GET /api/v1/collection/executions/{executionId}/logs` - 获取执行日志

### 监控统计

- `GET /api/v1/collection/monitor/statistics` - 获取统计信息

## 开发指南

### 添加新的数据源类型

1. 在 `DataSource.DataSourceType` 枚举中添加新类型
2. 在 `DataXExecutionEngine` 中添加对应的Reader/Writer映射
3. 更新数据库表结构和初始化数据

### 自定义DataX插件

1. 将插件放置在 `/runtime/datax/plugin` 目录下
2. 在 `DataXExecutionEngine` 中配置插件映射关系
3. 根据插件要求调整配置模板

### 扩展监控指标

1. 在 `StatisticsService` 中添加新的统计逻辑
2. 更新 `CollectionStatistics` DTO
3. 在数据库中添加相应的统计表或字段

## 故障排查

### 常见问题

1. **DataX执行失败**
   - 检查DataX安装路径和Python环境
   - 确认数据源连接配置正确
   - 查看执行日志获取详细错误信息

2. **数据库连接失败**
   - 检查数据库配置和网络连通性
   - 确认数据库用户权限

3. **API调用失败**
   - 检查请求参数格式
   - 查看应用日志获取详细错误信息

### 日志查看

```bash
# 应用日志
tail -f logs/data-collection-service.log

# 任务执行日志
curl http://localhost:8090/api/v1/collection/executions/{executionId}/logs
```

## 贡献指南

1. Fork项目
2. 创建特性分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -am 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 提交Pull Request

## 许可证

MIT License
