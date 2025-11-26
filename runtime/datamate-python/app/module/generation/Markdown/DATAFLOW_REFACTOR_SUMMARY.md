# QA对生成模块 - 数据流程重构总结

## 重构概述

根据您的需求，已完成整个QA对生成模块的数据流程重构，实现了从数据库读取、处理、存储到导出的完整链路。

## 新的数据流程

```
t_dm_dataset_files (源.txt文件)
          ↓
   文本切片 + QA生成
          ↓
t_qa_pairs (存储QA对: text_chunk, question, answer)
          ↓
  导出为JSONL文件
          ↓
t_dm_dataset_files (目标.jsonl文件)
```

## 主要变更

### 1. 数据库表结构

#### 新增: `t_qa_pairs` 表
用于存储所有生成的问答对，三列核心结构:
- `text_chunk` TEXT - 文本块内容
- `question` TEXT - 问题  
- `answer` TEXT - 答案

#### 更新: `t_qa_generation_instances` 表
新增字段:
- `total_files` INT - 总文件数
- `processed_files` INT - 已处理文件数

### 2. Service 层完全重写

**文件**: `app/module/generation/service/qa_generation.py`

新增核心方法:
- `get_source_files()` - 从 t_dm_dataset_files 获取源文件
- `save_qa_pair()` - 保存QA对到 t_qa_pairs
- `export_qa_pairs_to_jsonl()` - 导出JSONL文件
- `save_jsonl_to_dataset()` - 保存JSONL到目标数据集
- `process_task()` - 完整的任务执行流程

**处理流程**:
1. 从源数据集读取所有 .txt 文件
2. 逐文件进行文本切片和QA生成
3. 将QA对存入 t_qa_pairs 表
4. 按源文件导出对应的 .jsonl 文件 (abc.txt → abc.jsonl)
5. 将 .jsonl 文件记录到目标数据集

### 3. 数据库模型更新

**文件**: `app/db/models/qa_generation.py`

新增模型:
```python
class QAPair(Base):
    """QA对数据表"""
    __tablename__ = "t_qa_pairs"
    
    id = Column(String(64), primary_key=True)
    task_id = Column(String(64), nullable=False)
    source_file_id = Column(String(64), nullable=False)
    source_file_name = Column(String(255), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text_chunk = Column(Text, nullable=False)  # 文本块
    question = Column(Text, nullable=False)     # 问题
    answer = Column(Text, nullable=False)       # 答案
    # ... 其他字段
```

### 4. Schema 层更新

**文件**: `app/module/generation/schema/qa_generation.py`

更新响应模型，新增字段:
- `total_files` - 总文件数
- `processed_files` - 已处理文件数

### 5. Interface 层调整

**文件**: `app/module/generation/interface/qa_generation.py`

- 更新目标数据集创建逻辑 (类型标记为 "QA")
- 更新响应字段以包含文件处理进度

### 6. SQL 初始化脚本

**文件**: `scripts/db/qa-generation-init.sql`

新增 `t_qa_pairs` 表的创建语句。

## 文件列表

### 核心代码文件
- ✅ `app/db/models/qa_generation.py` - 数据库模型 (QAGenerationInstance + QAPair)
- ✅ `app/module/generation/service/qa_generation.py` - 业务逻辑服务
- ✅ `app/module/generation/service/text_splitter.py` - 文本切片工具
- ✅ `app/module/generation/schema/qa_generation.py` - 数据模型
- ✅ `app/module/generation/interface/qa_generation.py` - API路由

### 数据库脚本
- ✅ `scripts/db/qa-generation-init.sql` - 数据库初始化

### 文档
- ✅ `app/module/generation/DATA_FLOW.md` - 完整数据流程文档 ⭐ 新增
- ✅ `app/module/generation/README.md` - 功能文档
- ✅ `app/module/generation/QUICKSTART.md` - 快速入门
- ✅ `app/module/generation/LOCAL_FILE_USAGE.md` - 本地文件使用指南
- ✅ `app/module/generation/SUMMARY.md` - 开发总结
- ✅ `app/module/generation/DATAFLOW_REFACTOR_SUMMARY.md` - 本文件

### 测试
- ✅ `app/module/generation/test_qa_generation.py` - 单元测试

## 完整数据流示例

### 输入 (源数据集)

**t_dm_datasets**:
```
id: ds_001
name: "骆驼祥子原文"
type: "TEXT"
```

**t_dm_dataset_files**:
```
dataset_id: ds_001
files:
  - chapter1.txt (100KB)
  - chapter2.txt (95KB)
  - chapter3.txt (110KB)
```

### 处理过程

1. **读取文件** → chapter1.txt
2. **文本切片** → 120个文本块
3. **QA生成** → 每块生成2-3个QA对
4. **存储QA** → 280条QA对记录存入 t_qa_pairs
5. **导出JSONL** → chapter1.jsonl (280行)
6. **保存记录** → chapter1.jsonl 记录到目标数据集

### 输出 (目标数据集)

**t_dm_datasets**:
```
id: ds_002
name: "骆驼祥子QA数据集_QA_JSONL"
type: "QA"
format: "JSONL"
```

**t_dm_dataset_files**:
```
dataset_id: ds_002
files:
  - chapter1.jsonl (150KB, 280个QA对)
  - chapter2.jsonl (140KB, 260个QA对)
  - chapter3.jsonl (155KB, 295个QA对)
```

**t_qa_pairs**:
```
task_id: task_123
total_records: 835 (280 + 260 + 295)

每条记录格式:
{
  text_chunk: "祥子是一个人力车夫...",
  question: "祥子的职业是什么？",
  answer: "祥子的职业是人力车夫。"
}
```

## 使用方式

### 1. 初始化数据库

```bash
mysql -u root -p < scripts/db/qa-generation-init.sql
```

### 2. 创建QA生成任务

```bash
curl -X POST "http://localhost:8000/api/generation/qa-generation" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "骆驼祥子QA生成",
    "sourceDatasetId": "ds_001",
    "textSplitConfig": {
      "max_characters": 50000,
      "chunk_size": 800,
      "chunk_overlap": 200
    },
    "qaGenerationConfig": {
      "max_questions": 3,
      "temperature": 0.3,
      "model": "gpt-5-nano"
    },
    "llmApiKey": "sk-xxxxx",
    "llmBaseUrl": "https://api.openai.com/v1"
  }'
```

### 3. 监控进度

```bash
curl "http://localhost:8000/api/generation/qa-generation/{task_id}"
```

**响应**:
```json
{
  "status": "RUNNING",
  "total_files": 3,
  "processed_files": 1,
  "total_chunks": 350,
  "processed_chunks": 120,
  "total_qa_pairs": 280
}
```

### 4. 获取结果

任务完成后:
- QA对数据: 查询 `t_qa_pairs` 表
- JSONL文件: 从 `t_dm_dataset_files` 获取文件路径

## 进度追踪

系统实时追踪以下指标:

| 指标 | 说明 | 示例 |
|------|------|------|
| total_files | 源数据集.txt文件总数 | 3 |
| processed_files | 已处理完成的文件数 | 1 |
| total_chunks | 所有文件切片总数 | 350 |
| processed_chunks | 已生成QA的块数 | 120 |
| total_qa_pairs | 生成的QA对总数 | 280 |

**进度百分比**:
```
文件进度 = processed_files / total_files * 100%
块进度 = processed_chunks / total_chunks * 100%
```

## 关键特性

✅ **完整的数据库驱动流程** - 所有数据从数据库读取和写入
✅ **三列QA存储** - text_chunk, question, answer 清晰结构
✅ **JSONL格式导出** - 每个源文件对应一个JSONL文件
✅ **文件名映射** - abc.txt自动生成abc.jsonl
✅ **数据集管理** - 源和目标都是标准数据集
✅ **进度实时追踪** - 文件级和块级双重进度
✅ **错误容错** - 单文件失败不影响其他文件
✅ **数据持久化** - QA对永久存储在t_qa_pairs表

## 与之前版本的对比

| 特性 | 旧版本 | 新版本 |
|------|--------|--------|
| 数据源 | 本地文件/数据集ID | t_dm_dataset_files表 |
| QA存储 | 直接导出文件 | t_qa_pairs表 (三列) |
| 输出格式 | 单个JSONL | 每文件独立JSONL |
| 文件管理 | 手动管理 | t_dm_dataset_files表 |
| 进度追踪 | 只有块级进度 | 文件+块双重进度 |
| 数据持久化 | 仅文件 | 数据库+文件双重 |

## 后续优化建议

1. **批量插入优化** - 使用批量插入提升t_qa_pairs写入性能
2. **异步导出** - JSONL导出可以后台异步进行
3. **压缩存储** - 大文件JSONL可以压缩存储
4. **增量更新** - 支持仅处理新增文件
5. **QA质量评估** - 添加质量分数字段
6. **去重功能** - 检测并去除重复的QA对

## 故障排查

### 问题1: 找不到源文件
**原因**: t_dm_dataset_files中没有.txt文件
**解决**: 确保源数据集中有file_type为'txt'的活跃文件

### 问题2: JSONL文件未生成
**原因**: t_qa_pairs中没有数据
**解决**: 检查LLM调用是否成功，查看error_message

### 问题3: 文件路径错误
**原因**: t_dm_dataset_files中的file_path不存在
**解决**: 确保file_path指向实际存在的文件

## 总结

本次重构完全实现了您要求的数据流动：

1. ✅ 从 t_dm_dataset_files 读取源.txt文件
2. ✅ QA对存储到 t_qa_pairs (三列: text_chunk, question, answer)
3. ✅ 转换为JSONL格式
4. ✅ 按原文件名生成对应JSONL (abc.txt → abc.jsonl)
5. ✅ 保存到目标数据集的 t_dm_dataset_files

所有代码已完成，数据流程清晰可追踪！
