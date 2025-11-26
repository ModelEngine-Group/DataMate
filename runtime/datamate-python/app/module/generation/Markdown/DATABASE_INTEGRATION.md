# QA生成模块 - DataMate数据库集成说明

## 数据库架构

所有表都在同一个 **`datamate`** 数据库中，实现完整的数据流集成。

## 表关系图

```
datamate 数据库
├── t_dm_datasets (数据集表)
│   ├── id VARCHAR(36) PRIMARY KEY
│   ├── name VARCHAR(255)
│   ├── dataset_type VARCHAR(50) [IMAGE/TEXT/QA/MULTIMODAL/OTHER]
│   └── ...
│
├── t_dm_dataset_files (数据集文件表)
│   ├── id VARCHAR(36) PRIMARY KEY
│   ├── dataset_id VARCHAR(36) → t_dm_datasets.id
│   ├── file_name VARCHAR(255)
│   ├── file_path VARCHAR(1000)
│   ├── file_type VARCHAR(50) [txt/jsonl/jpg/png/...]
│   └── ...
│
├── t_qa_generation_instances (QA生成任务表)
│   ├── id VARCHAR(36) PRIMARY KEY
│   ├── source_dataset_id VARCHAR(36) → t_dm_datasets.id
│   ├── target_dataset_id VARCHAR(36) → t_dm_datasets.id
│   ├── total_files INT
│   ├── processed_files INT
│   └── ...
│
└── t_qa_pairs (QA对数据表)
    ├── id VARCHAR(36) PRIMARY KEY
    ├── task_id VARCHAR(36) → t_qa_generation_instances.id
    ├── source_file_id VARCHAR(36) → t_dm_dataset_files.id
    ├── text_chunk TEXT
    ├── question TEXT
    ├── answer TEXT
    └── ...
```

## 完整数据流

### 步骤1: 准备源数据集

在 `t_dm_datasets` 中创建源数据集：
```sql
INSERT INTO t_dm_datasets (id, name, dataset_type, format, status)
VALUES (
    'ds-source-001',
    '骆驼祥子原文',
    'TEXT',
    'TXT',
    'ACTIVE'
);
```

在 `t_dm_dataset_files` 中添加 .txt 文件：
```sql
INSERT INTO t_dm_dataset_files (id, dataset_id, file_name, file_path, file_type, status)
VALUES 
    ('file-001', 'ds-source-001', 'chapter1.txt', '/data/luotuo/chapter1.txt', 'txt', 'ACTIVE'),
    ('file-002', 'ds-source-001', 'chapter2.txt', '/data/luotuo/chapter2.txt', 'txt', 'ACTIVE'),
    ('file-003', 'ds-source-001', 'chapter3.txt', '/data/luotuo/chapter3.txt', 'txt', 'ACTIVE');
```

### 步骤2: 创建QA生成任务

调用API创建任务：
```bash
POST /api/generation/qa-generation
{
    "name": "骆驼祥子QA生成",
    "sourceDatasetId": "ds-source-001",  # 引用 t_dm_datasets.id
    "textSplitConfig": {...},
    "qaGenerationConfig": {...}
}
```

系统自动：
1. 在 `t_dm_datasets` 创建目标数据集（dataset_type='QA', format='JSONL'）
2. 在 `t_qa_generation_instances` 创建任务记录
3. 设置外键关联：source_dataset_id 和 target_dataset_id

### 步骤3: 任务执行

后台任务自动执行：

#### 3.1 读取源文件
```python
# 从 t_dm_dataset_files 查询
files = await db.execute(
    select(DatasetFiles)
    .where(DatasetFiles.dataset_id == source_dataset_id)
    .where(DatasetFiles.file_type == 'txt')
    .where(DatasetFiles.status == 'ACTIVE')
)
```

#### 3.2 生成QA对并存储
```python
# 每个文本块生成QA后，存入 t_qa_pairs
qa_pair = QAPair(
    task_id=task_id,                    # → t_qa_generation_instances.id
    source_file_id=source_file.id,      # → t_dm_dataset_files.id
    source_file_name=source_file.file_name,
    chunk_index=chunk_idx,
    text_chunk=chunk_text,
    question=question,
    answer=answer
)
await db.add(qa_pair)
```

#### 3.3 导出JSONL
```python
# 从 t_qa_pairs 读取数据，按源文件分组导出
qa_pairs = await db.execute(
    select(QAPair)
    .where(QAPair.task_id == task_id)
    .where(QAPair.source_file_id == file_id)
    .order_by(QAPair.chunk_index)
)

# 生成 JSONL 文件：chapter1.txt → chapter1.jsonl
```

#### 3.4 保存到目标数据集
```python
# 将 .jsonl 文件记录插入 t_dm_dataset_files
dataset_file = DatasetFiles(
    dataset_id=target_dataset_id,       # → t_dm_datasets.id
    file_name='chapter1.jsonl',
    file_path='/data/qa_output/chapter1.jsonl',
    file_type='jsonl',
    status='ACTIVE'
)
await db.add(dataset_file)
```

### 步骤4: 结果查询

#### 查看任务进度
```sql
SELECT 
    id, name, status,
    processed_files, total_files,
    processed_chunks, total_chunks,
    total_qa_pairs
FROM t_qa_generation_instances
WHERE id = 'task-123';
```

#### 查看生成的QA对
```sql
SELECT 
    source_file_name,
    chunk_index,
    text_chunk,
    question,
    answer
FROM t_qa_pairs
WHERE task_id = 'task-123'
ORDER BY source_file_name, chunk_index;
```

#### 查看目标数据集文件
```sql
SELECT 
    f.file_name,
    f.file_path,
    f.file_size,
    d.name as dataset_name
FROM t_dm_dataset_files f
JOIN t_dm_datasets d ON f.dataset_id = d.id
WHERE d.id = 'ds-target-002'
  AND f.file_type = 'jsonl'
  AND f.status = 'ACTIVE';
```

## 数据示例

### 源数据集 (TEXT类型)
**t_dm_datasets**:
```
id: ds-source-001
name: 骆驼祥子原文
dataset_type: TEXT
format: TXT
status: ACTIVE
```

**t_dm_dataset_files**:
```
id              | dataset_id    | file_name      | file_type | status
----------------|---------------|----------------|-----------|--------
file-001        | ds-source-001 | chapter1.txt   | txt       | ACTIVE
file-002        | ds-source-001 | chapter2.txt   | txt       | ACTIVE
file-003        | ds-source-001 | chapter3.txt   | txt       | ACTIVE
```

### QA生成任务
**t_qa_generation_instances**:
```
id: task-123
name: 骆驼祥子QA生成
source_dataset_id: ds-source-001  (→ t_dm_datasets.id)
target_dataset_id: ds-target-002  (→ t_dm_datasets.id)
status: RUNNING
total_files: 3
processed_files: 1
total_chunks: 350
processed_chunks: 120
total_qa_pairs: 280
```

### QA对数据
**t_qa_pairs**:
```
id       | task_id  | source_file_id | source_file_name | chunk_index | text_chunk              | question              | answer
---------|----------|----------------|------------------|-------------|-------------------------|-----------------------|--------
qa-001   | task-123 | file-001       | chapter1.txt     | 0           | 祥子是一个人力车夫...   | 祥子的职业是什么？    | 祥子的职业是人力车夫
qa-002   | task-123 | file-001       | chapter1.txt     | 0           | 祥子是一个人力车夫...   | 祥子住在哪里？        | 祥子住在北京
qa-003   | task-123 | file-001       | chapter1.txt     | 1           | 他每天早上五点起床...   | 祥子几点起床？        | 祥子每天早上五点起床
...
```

### 目标数据集 (QA类型)
**t_dm_datasets**:
```
id: ds-target-002
name: 骆驼祥子QA数据集_QA_JSONL
dataset_type: QA
format: JSONL
status: ACTIVE
```

**t_dm_dataset_files**:
```
id              | dataset_id    | file_name        | file_type | status
----------------|---------------|------------------|-----------|--------
file-101        | ds-target-002 | chapter1.jsonl   | jsonl     | ACTIVE
file-102        | ds-target-002 | chapter2.jsonl   | jsonl     | ACTIVE
file-103        | ds-target-002 | chapter3.jsonl   | jsonl     | ACTIVE
```

## 外键约束

数据库通过外键保证数据一致性：

```sql
-- t_qa_generation_instances 的外键
FOREIGN KEY (source_dataset_id) REFERENCES t_dm_datasets(id) ON DELETE RESTRICT
FOREIGN KEY (target_dataset_id) REFERENCES t_dm_datasets(id) ON DELETE RESTRICT

-- t_qa_pairs 的外键
FOREIGN KEY (task_id) REFERENCES t_qa_generation_instances(id) ON DELETE CASCADE
FOREIGN KEY (source_file_id) REFERENCES t_dm_dataset_files(id) ON DELETE CASCADE

-- t_dm_dataset_files 的外键
FOREIGN KEY (dataset_id) REFERENCES t_dm_datasets(id) ON DELETE CASCADE
```

### 外键行为说明

- **RESTRICT**: 删除数据集时，如果有QA任务引用则阻止删除
- **CASCADE**: 删除任务时，自动删除所有关联的QA对数据
- **CASCADE**: 删除数据集时，自动删除所有关联的文件记录

## 数据一致性检查

### 检查孤立的QA对
```sql
-- 找到没有对应源文件的QA对
SELECT qp.*
FROM t_qa_pairs qp
LEFT JOIN t_dm_dataset_files df ON qp.source_file_id = df.id
WHERE df.id IS NULL;
```

### 检查任务与数据集的对应
```sql
-- 找到引用了不存在数据集的任务
SELECT qi.*
FROM t_qa_generation_instances qi
LEFT JOIN t_dm_datasets ds ON qi.source_dataset_id = ds.id
WHERE ds.id IS NULL;
```

### 统计数据集的QA生成情况
```sql
-- 统计每个数据集被用作源的次数
SELECT 
    d.id,
    d.name,
    COUNT(qi.id) as task_count,
    SUM(qi.total_qa_pairs) as total_qa_pairs
FROM t_dm_datasets d
LEFT JOIN t_qa_generation_instances qi ON d.id = qi.source_dataset_id
GROUP BY d.id, d.name;
```

## 初始化脚本

执行以下命令初始化QA生成模块的表：

```bash
mysql -u root -p datamate < scripts/db/qa-generation-init.sql
```

脚本会自动：
1. 使用 `USE datamate;` 切换到正确的数据库
2. 创建 `t_qa_generation_instances` 表（带外键约束）
3. 创建 `t_qa_pairs` 表（带外键约束）
4. 建立所有必要的索引

## 数据库模型对应

Python SQLAlchemy 模型与数据库表的对应关系：

| Python 模型 | 数据库表 | 模块 |
|------------|----------|------|
| `Dataset` | `t_dm_datasets` | `app.db.models.dataset_management` |
| `DatasetFiles` | `t_dm_dataset_files` | `app.db.models.dataset_management` |
| `QAGenerationInstance` | `t_qa_generation_instances` | `app.db.models.qa_generation` |
| `QAPair` | `t_qa_pairs` | `app.db.models.qa_generation` |

所有模型的 ID 字段统一使用 `VARCHAR(36)` 存储 UUID。

## 关键特性

✅ **统一数据库** - 所有表在同一个 datamate 数据库中
✅ **外键约束** - 保证数据引用完整性
✅ **UUID主键** - 所有表使用 VARCHAR(36) 存储 UUID
✅ **级联删除** - 删除任务自动清理QA对数据
✅ **状态追踪** - 完整的文件级和块级进度追踪
✅ **数据复用** - QA对存储在 t_qa_pairs，可多次导出不同格式

## 与现有系统集成

QA生成模块完全集成到 DataMate 数据管理系统：

1. **数据源**: 从 `t_dm_dataset_files` 读取源文件
2. **数据存储**: QA对存入 `t_qa_pairs` 表
3. **结果输出**: 生成的 JSONL 文件记录到 `t_dm_dataset_files`
4. **数据集管理**: 源和目标都是标准的 `t_dm_datasets` 数据集
5. **统一API**: 通过 DataMate API 统一管理所有数据

## 注意事项

⚠️ **确保源数据集存在**: 创建任务前必须在 `t_dm_datasets` 中存在源数据集
⚠️ **文件路径有效**: `t_dm_dataset_files` 中的 `file_path` 必须指向实际存在的文件
⚠️ **文件类型过滤**: 只处理 `file_type='txt'` 且 `status='ACTIVE'` 的文件
⚠️ **数据库权限**: 确保应用有创建外键约束的权限
⚠️ **事务处理**: 大批量QA对插入建议使用批量插入优化性能
