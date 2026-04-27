# DataX Framework

## Overview

DataX is a data transfer framework that supports data transmission between various data sources and targets, used for data collection and synchronization.

## Architecture

```
runtime/datax/
├── core/           # DataX core components
├── transformer/     # Data transformers
├── readers/        # Data readers
│   ├── mysqlreader/
│   ├── postgresqlreader/
│   ├── oracleReader/
│   ├── mongodbreader/
│   ├── hdfsreader/
│   ├── s3rader/
│   ├── nfsreader/
│   ├── glusterfsreader/
│   └── apireader/
└── writers/        # Data writers
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

## Supported Data Sources

### Relational Databases
- MySQL
- PostgreSQL
- Oracle
- SQL Server
- DB2
- KingbaseES
- GaussDB

### NoSQL Databases
- MongoDB
- Elasticsearch
- Cassandra
- HBase
- Redis

### File Systems
- HDFS
- S3 (AWS S3, MinIO, Alibaba Cloud OSS)
- NFS
- GlusterFS
- Local file system

### Others
- API interfaces
- Kafka
- Pulsar
- DataHub
- LogHub

## Usage

### Basic Configuration
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

### Run DataX
```bash
# Build DataX
cd runtime/datax
mvn clean package

# Run
python datax.py -j job.json
```

## Quick Start

### Prerequisites
- JDK 8+
- Maven 3.8+
- Python 3.6+

### Build
```bash
cd runtime/datax
mvn clean package
```

### Run Example
```bash
python datax.py -j examples/mysql2text.json
```

## Development

### Adding a New Reader
1. Create new module in `readers/`
2. Implement Reader interface
3. Configure reader parameters
4. Add to package.xml

### Adding a New Writer
1. Create new module in `writers/`
2. Implement Writer interface
3. Configure writer parameters
4. Add to package.xml

## Documentation

- [DataX Official Documentation](https://github.com/alibaba/DataX)

## Related Links

- [Runtime README](../README.md)
