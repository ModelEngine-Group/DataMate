# DataX 框架

## 概述

DataX 是一个数据传输框架，支持多种数据源和数据目标之间的数据传输，用于数据收集和同步。

## 架构

```
runtime/datax/
├── core/           # DataX 核心组件
├── transformer/     # 数据转换器
├── readers/        # 数据读取器
│   ├── mysqlreader/
│   ├── postgresqlreader/
│   ├── oracleReader/
│   ├── mongodbreader/
│   ├── hdfsreader/
│   ├── s3rader/
│   ├── nfsreader/
│   ├── glusterfsreader/
│   └── apireader/
└── writers/        # 数据写入器
    ├── mysqlwriter/
    ├── postgresqlwriter/
    ├── oraclewriter/
    ├── mongodbwriter/
    ├── hdfswriter/
    ├── s3writer/
    ├── nfswriter/
    ├── glusterfswriter/
    └── txtfilewriter/
```

## 支持的数据源

### 关系型数据库
- MySQL
- PostgreSQL
- Oracle
- SQL Server
- DB2
- KingbaseES
- GaussDB

### NoSQL 数据库
- MongoDB
- Elasticsearch
- Cassandra
- HBase
- Redis

### 文件系统
- HDFS
- S3 (AWS S3, MinIO, 阿里云 OSS)
- NFS
- GlusterFS
- 本地文件系统

### 其他
- API 接口
- Kafka
- Pulsar
- DataHub
- LogHub

## 使用

### 基本配置
```json
{
  "job": {
    "content": [
      {
        "reader": {
          "name": "mysqlreader",
          "parameter": {
            "username": "root",
            "password": "password",
            "column": ["id", "name", "email"],
            "connection": [
              {
                "jdbcUrl": "jdbc:mysql://localhost:3306/database",
                "table": ["users"]
              }
            ]
          }
        },
        "writer": {
          "name": "txtfilewriter",
          "parameter": {
            "path": "/output/users.txt",
            "fileName": "users",
            "writeMode": "truncate"
          }
        }
      }
    ]
  }
}
```

### 运行 DataX
```bash
# 构建 DataX
cd runtime/datax
mvn clean package

# 运行
python datax.py -j job.json
```

## 快速开始

### 前置条件
- JDK 8+
- Maven 3.8+
- Python 3.6+

### 构建
```bash
cd runtime/datax
mvn clean package
```

### 运行示例
```bash
python datax.py -j examples/mysql2text.json
```

## 开发

### 添加新的 Reader
1. 在 `readers/` 创建新模块
2. 实现 Reader 接口
3. 配置 reader 参数
4. 添加到 package.xml

### 添加新的 Writer
1. 在 `writers/` 创建新模块
2. 实现 Writer 接口
3. 配置 writer 参数
4. 添加到 package.xml

## 文档

- [DataX 官方文档](https://github.com/alibaba/DataX)

## 相关链接

- [运行时 README](../README.md)
