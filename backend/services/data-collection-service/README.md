# 数据归集服务架构设计

## 服务概述

数据归集服务（data-collection-service）是基于DataX的数据采集和归集模块，负责从多种异构数据源中采集数据并归集到目标数据源。

### 主要功能

1. **多数据源支持**：支持关系型数据库、NoSQL数据库、大数据存储、消息队列等多种数据源
2. **DataX集成**：基于阿里巴巴DataX引擎，提供高性能的数据同步能力
3. **任务管理**：提供数据归集任务的创建、配置、执行、监控等功能
4. **连接测试**：支持数据源连接的测试和验证
5. **实时监控**：提供任务执行状态、进度、日志等实时监控

## 技术架构

### DDD分层架构

```
com.dataengine.collection/
├── domain/                     # 领域层
│   ├── model/                 # 领域模型
│   │   ├── DataSource.java           # 数据源聚合根
│   │   ├── DataSourceId.java         # 数据源标识
│   │   ├── DataSourceType.java       # 数据源类型枚举
│   │   ├── DataSourceStatus.java     # 数据源状态枚举
│   │   ├── CollectionTask.java       # 归集任务聚合根
│   │   ├── CollectionTaskId.java     # 归集任务标识
│   │   └── TaskStatus.java           # 任务状态枚举
│   ├── repository/            # 仓储接口
│   │   ├── DataSourceRepository.java
│   │   └── CollectionTaskRepository.java
│   └── service/               # 领域服务
│       ├── DataXDomainService.java   # DataX领域服务
│       └── DataXJobStatus.java       # DataX作业状态
├── application/               # 应用层
│   ├── service/              # 应用服务
│   │   ├── DataSourceApplicationService.java
│   │   ├── CollectionTaskApplicationService.java
│   │   └── DataSourceConnectionService.java
│   └── dto/                  # 数据传输对象
│       ├── DataSourceCreateDTO.java
│       ├── DataSourceUpdateDTO.java
│       ├── DataSourceDTO.java
│       └── ConnectionTestResultDTO.java
├── infrastructure/           # 基础设施层
│   ├── repository/          # 仓储实现
│   │   ├── JpaDataSourceRepository.java
│   │   └── JpaCollectionTaskRepository.java
│   ├── datax/              # DataX集成
│   │   ├── DataXEngineImpl.java
│   │   ├── DataXConfigGenerator.java
│   │   └── DataXJobManager.java
│   └── config/             # 配置类
│       └── DataCollectionConfig.java
└── interfaces/              # 接口层
    ├── rest/               # REST控制器
    │   ├── DataSourceController.java
    │   ├── CollectionTaskController.java
    │   └── MonitorController.java
    └── dto/                # 接口DTO（OpenAPI生成）
```

## 支持的数据源类型

| 数据源类型 | 说明 | DataX Reader/Writer |
|-----------|------|-------------------|
| MYSQL | MySQL数据库 | mysqlreader/mysqlwriter |
| POSTGRESQL | PostgreSQL数据库 | postgresqlreader/postgresqlwriter |
| ORACLE | Oracle数据库 | oraclereader/oraclewriter |
| SQLSERVER | SQL Server数据库 | sqlserverreader/sqlserverwriter |
| MONGODB | MongoDB文档数据库 | mongodbreader/mongodbwriter |
| REDIS | Redis缓存数据库 | redisreader/rediswriter |
| ELASTICSEARCH | Elasticsearch搜索引擎 | elasticsearchreader/elasticsearchwriter |
| HIVE | Hive数据仓库 | hivereader/hivewriter |
| HDFS | Hadoop分布式文件系统 | hdfsreader/hdfswriter |
| KAFKA | Apache Kafka消息队列 | kafkareader/kafkawriter |
| HTTP | HTTP API接口 | httpreader/httpwriter |
| FILE | 文件系统 | txtfilereader/txtfilewriter |

## API接口设计

### 数据源管理
- `GET /api/v1/collection/datasources` - 获取数据源列表
- `POST /api/v1/collection/datasources` - 创建数据源
- `GET /api/v1/collection/datasources/{id}` - 获取数据源详情
- `PUT /api/v1/collection/datasources/{id}` - 更新数据源
- `DELETE /api/v1/collection/datasources/{id}` - 删除数据源
- `POST /api/v1/collection/datasources/{id}/test` - 测试数据源连接

### 归集任务管理
- `GET /api/v1/collection/tasks` - 获取归集任务列表
- `POST /api/v1/collection/tasks` - 创建归集任务
- `GET /api/v1/collection/tasks/{id}` - 获取归集任务详情
- `PUT /api/v1/collection/tasks/{id}` - 更新归集任务
- `POST /api/v1/collection/tasks/{id}/execute` - 执行归集任务
- `POST /api/v1/collection/tasks/{id}/stop` - 停止归集任务

### DataX作业管理
- `GET /api/v1/collection/datax/jobs` - 获取DataX作业列表
- `POST /api/v1/collection/datax/jobs` - 创建DataX作业
- `GET /api/v1/collection/datax/jobs/{id}/config` - 获取DataX作业配置

### 监控与统计
- `GET /api/v1/collection/monitor/tasks/{id}/status` - 获取任务执行状态
- `GET /api/v1/collection/monitor/tasks/{id}/logs` - 获取任务执行日志
- `GET /api/v1/collection/monitor/statistics` - 获取归集统计信息

## 数据模型

### 数据源模型
```java
DataSource {
    DataSourceId id;           // 数据源ID
    String name;              // 数据源名称
    DataSourceType type;      // 数据源类型
    String description;       // 描述信息
    Map<String, String> config; // 连接配置
    DataSourceStatus status;  // 数据源状态
    LocalDateTime createdAt;  // 创建时间
    LocalDateTime updatedAt;  // 更新时间
}
```

### 归集任务模型
```java
CollectionTask {
    CollectionTaskId id;              // 任务ID
    String name;                      // 任务名称
    String description;               // 任务描述
    DataSourceId sourceDataSourceId; // 源数据源ID
    DataSourceId targetDataSourceId; // 目标数据源ID
    Map<String, String> config;      // 归集配置
    TaskStatus status;                // 任务状态
    String scheduleExpression;        // 调度表达式
    String lastExecutionId;          // 最后执行ID
    LocalDateTime createdAt;         // 创建时间
    LocalDateTime updatedAt;         // 更新时间
}
```

## DataX集成架构

### DataX配置生成
根据源数据源和目标数据源的类型，自动生成DataX的JSON配置文件：

```json
{
  "job": {
    "setting": {
      "speed": {
        "channel": 1
      }
    },
    "content": [
      {
        "reader": {
          "name": "mysqlreader",
          "parameter": {
            "username": "source_user",
            "password": "source_pass",
            "connection": [
              {
                "jdbcUrl": ["jdbc:mysql://source:3306/db"],
                "table": ["source_table"]
              }
            ],
            "column": ["*"]
          }
        },
        "writer": {
          "name": "mysqlwriter",
          "parameter": {
            "username": "target_user",
            "password": "target_pass",
            "connection": [
              {
                "jdbcUrl": "jdbc:mysql://target:3306/db",
                "table": ["target_table"]
              }
            ],
            "column": ["*"]
          }
        }
      }
    ]
  }
}
```

### DataX执行流程
1. **任务创建**：用户创建归集任务，配置源和目标数据源
2. **配置生成**：系统根据数据源信息生成DataX配置
3. **任务执行**：调用DataX引擎执行数据同步
4. **状态监控**：实时监控任务执行状态和进度
5. **结果处理**：处理执行结果，更新任务状态

## 部署配置

### Maven依赖
```xml
<dependencies>
    <!-- DataX核心依赖 -->
    <dependency>
        <groupId>com.alibaba.datax</groupId>
        <artifactId>datax-core</artifactId>
        <version>3.0</version>
    </dependency>
    
    <!-- 数据库驱动依赖 -->
    <dependency>
        <groupId>mysql</groupId>
        <artifactId>mysql-connector-java</artifactId>
    </dependency>
    <!-- 其他数据源驱动... -->
</dependencies>
```

### 环境变量
- `DATAX_HOME`: DataX安装目录
- `DATAX_PYTHON`: Python解释器路径（用于DataX执行）

### 应用配置
```yaml
datax:
  home: ${DATAX_HOME:/opt/datax}
  python: ${DATAX_PYTHON:/usr/bin/python}
  job:
    max-parallel: 5
    timeout: 3600
  temp:
    dir: /tmp/datax-jobs
```

## 扩展点

### 自定义数据源支持
1. 实现DataSourceType新枚举值
2. 扩展DataXConfigGenerator支持新的Reader/Writer
3. 添加相应的连接测试逻辑

### 自定义调度策略
1. 实现ScheduleStrategy接口
2. 扩展CollectionTask支持新的调度表达式
3. 集成Spring Scheduler或Quartz

### 监控告警扩展
1. 集成Prometheus指标收集
2. 实现自定义告警规则
3. 支持钉钉、邮件等告警通知

## 使用示例

### 创建MySQL到PostgreSQL的数据归集任务

1. **创建源数据源**
```bash
curl -X POST /api/v1/collection/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mysql-source",
    "type": "MYSQL",
    "description": "MySQL源数据库",
    "config": {
      "host": "mysql.example.com",
      "port": "3306",
      "database": "source_db",
      "username": "user",
      "password": "pass"
    }
  }'
```

2. **创建目标数据源**
```bash
curl -X POST /api/v1/collection/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "postgresql-target",
    "type": "POSTGRESQL",
    "description": "PostgreSQL目标数据库",
    "config": {
      "host": "postgres.example.com",
      "port": "5432",
      "database": "target_db",
      "username": "user",
      "password": "pass"
    }
  }'
```

3. **创建归集任务**
```bash
curl -X POST /api/v1/collection/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mysql-to-postgres-sync",
    "description": "MySQL到PostgreSQL数据同步",
    "sourceDataSourceId": "source-id",
    "targetDataSourceId": "target-id",
    "config": {
      "sourceTable": "users",
      "targetTable": "users",
      "syncMode": "full",
      "batchSize": "1000"
    },
    "schedule": "0 0 2 * * ?"
  }'
```

4. **执行归集任务**
```bash
curl -X POST /api/v1/collection/tasks/{task-id}/execute
```

通过这个完整的数据归集服务，平台可以支持多种数据源之间的高效数据同步和归集，为后续的数据处理和分析提供统一的数据接入能力。
