# QA生成模块 - 测试指南

## 前置准备

### 1. 初始化数据库

```bash
# 进入MySQL
mysql -u root -p

# 创建或使用datamate数据库
CREATE DATABASE IF NOT EXISTS datamate;
USE datamate;

# 执行数据管理模块的初始化（如果还没执行）
source scripts/db/data-management-init.sql;

# 执行QA生成模块的初始化
source scripts/db/qa-generation-init.sql;
```

### 2. 准备测试数据

#### 2.1 创建源数据集

```sql
-- 插入源数据集
INSERT INTO t_dm_datasets (id, name, description, dataset_type, format, status)
VALUES (
    'test-dataset-001',
    '测试文本数据集',
    '用于测试QA生成的文本数据集',
    'TEXT',
    'TXT',
    'ACTIVE'
);
```

#### 2.2 创建测试文本文件

在服务器上创建测试文件：

```bash
# 创建测试目录
mkdir -p /data/test-qa-generation

# 创建测试文件1
cat > /data/test-qa-generation/sample1.txt << 'EOF'
人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。

机器学习是人工智能的一个重要分支。通过算法使计算机能够从数据中学习，并自动改进。深度学习是机器学习的一个子集，它使用神经网络来模拟人脑的学习过程。

近年来，人工智能在医疗、金融、教育等多个领域都取得了突破性进展。例如，AI可以帮助医生诊断疾病，帮助教师个性化教学，帮助金融机构进行风险评估。
EOF

# 创建测试文件2
cat > /data/test-qa-generation/sample2.txt << 'EOF'
Python是一种高级编程语言，由Guido van Rossum于1991年首次发布。Python的设计哲学强调代码的可读性和简洁的语法。

Python支持多种编程范式，包括面向对象、命令式、函数式和过程式编程。Python拥有一个庞大的标准库，涵盖了网络编程、文件操作、数据处理等多个方面。

Python在数据科学、机器学习、Web开发等领域都有广泛应用。常用的库包括NumPy、Pandas、Django、Flask等。
EOF
```

#### 2.3 插入文件记录到数据库

```sql
-- 插入测试文件记录
INSERT INTO t_dm_dataset_files (id, dataset_id, file_name, file_path, file_type, status, file_size)
VALUES 
    ('test-file-001', 'test-dataset-001', 'sample1.txt', '/data/test-qa-generation/sample1.txt', 'txt', 'ACTIVE', 500),
    ('test-file-002', 'test-dataset-001', 'sample2.txt', '/data/test-qa-generation/sample2.txt', 'txt', 'ACTIVE', 400);
```

### 3. 配置环境变量

```bash
# 设置OpenAI API配置
export OPENAI_API_KEY="sk-your-api-key-here"
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

---

## 测试方式

### 方式1: API测试（推荐）

#### 启动服务

```bash
cd runtime/datamate-python
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 1. 创建QA生成任务

```bash
curl -X POST "http://localhost:8000/api/generation/qa-generation" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试QA生成任务",
    "description": "这是一个测试任务",
    "sourceDatasetId": "test-dataset-001",
    "textSplitConfig": {
      "max_characters": 50000,
      "chunk_size": 300,
      "chunk_overlap": 50,
      "separators": ["\n\n", "\n", "。", "！", "？", ".", "!", "?"]
    },
    "qaGenerationConfig": {
      "max_questions": 2,
      "temperature": 0.3,
      "model": "gpt-3.5-turbo"
    },
    "llmApiKey": "sk-your-api-key-here",
    "llmBaseUrl": "https://api.openai.com/v1"
  }'
```

**响应示例**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "测试QA生成任务",
  "status": "PENDING",
  "sourceDatasetId": "test-dataset-001",
  "createdAt": "2025-11-20T10:30:00"
}
```

#### 2. 查询任务状态

```bash
# 获取任务ID后查询
curl "http://localhost:8000/api/generation/qa-generation/{task_id}"
```

**响应示例**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "测试QA生成任务",
  "status": "RUNNING",
  "totalFiles": 2,
  "processedFiles": 1,
  "totalChunks": 8,
  "processedChunks": 4,
  "totalQaPairs": 8,
  "progress": {
    "fileProgress": 50.0,
    "chunkProgress": 50.0
  }
}
```

#### 3. 查看生成的QA对

```bash
# 方式1: 直接查询数据库
mysql -u root -p datamate -e "
SELECT 
    source_file_name,
    chunk_index,
    LEFT(text_chunk, 50) as text_preview,
    question,
    answer
FROM t_qa_pairs
WHERE task_id = 'your-task-id'
ORDER BY source_file_name, chunk_index
LIMIT 10;
"

# 方式2: 查看导出的JSONL文件
cat /data/qa_output/sample1.jsonl | jq .
```

#### 4. 验证目标数据集

```bash
# 查询目标数据集的文件
mysql -u root -p datamate -e "
SELECT 
    f.file_name,
    f.file_path,
    f.file_type,
    f.file_size,
    d.name as dataset_name
FROM t_dm_dataset_files f
JOIN t_dm_datasets d ON f.dataset_id = d.id
JOIN t_qa_generation_instances qi ON d.id = qi.target_dataset_id
WHERE qi.id = 'your-task-id';
"
```

### 方式2: Python单元测试

```bash
cd runtime/datamate-python

# 运行单元测试
pytest app/module/generation/test_qa_generation.py -v

# 运行特定测试
pytest app/module/generation/test_qa_generation.py::test_create_task -v

# 查看测试覆盖率
pytest app/module/generation/test_qa_generation.py --cov=app.module.generation --cov-report=html
```

### 方式3: 交互式测试（IPython）

```python
# 启动IPython
ipython

# 导入必要的模块
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.module.generation.service.qa_generation import QAGenerationService
from app.db.models.qa_generation import QAGenerationInstance, QAPair
from sqlalchemy import select

# 创建异步数据库会话
DATABASE_URL = "mysql+aiomysql://root:password@localhost:3306/datamate"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 创建服务实例
async def test_qa_generation():
    async with async_session() as session:
        service = QAGenerationService(session)
        
        # 创建任务
        task = await service.create_task(
            name="交互式测试任务",
            description="通过IPython测试",
            source_dataset_id="test-dataset-001",
            text_split_config={
                "max_characters": 50000,
                "chunk_size": 300,
                "chunk_overlap": 50
            },
            qa_generation_config={
                "max_questions": 2,
                "temperature": 0.3,
                "model": "gpt-3.5-turbo"
            },
            llm_api_key="sk-your-api-key",
            llm_base_url="https://api.openai.com/v1"
        )
        
        print(f"Task created: {task.id}")
        
        # 执行任务
        await service.process_task(task.id)
        
        # 查询结果
        result = await service.get_task_by_id(task.id)
        print(f"Status: {result.status}")
        print(f"QA Pairs: {result.total_qa_pairs}")
        
        return task.id

# 运行测试
import asyncio
task_id = asyncio.run(test_qa_generation())
```

---

## 验证检查清单

### ✅ 数据库检查

```sql
-- 1. 检查任务是否创建
SELECT * FROM t_qa_generation_instances WHERE id = 'your-task-id';

-- 2. 检查QA对是否生成
SELECT COUNT(*) FROM t_qa_pairs WHERE task_id = 'your-task-id';

-- 3. 检查每个文件的QA对数量
SELECT 
    source_file_name,
    COUNT(*) as qa_count
FROM t_qa_pairs
WHERE task_id = 'your-task-id'
GROUP BY source_file_name;

-- 4. 检查目标数据集是否创建
SELECT * FROM t_dm_datasets 
WHERE id = (SELECT target_dataset_id FROM t_qa_generation_instances WHERE id = 'your-task-id');

-- 5. 检查JSONL文件是否记录
SELECT * FROM t_dm_dataset_files 
WHERE dataset_id = (SELECT target_dataset_id FROM t_qa_generation_instances WHERE id = 'your-task-id');
```

### ✅ 文件系统检查

```bash
# 检查JSONL文件是否生成
ls -lh /data/qa_output/*.jsonl

# 查看JSONL文件内容
cat /data/qa_output/sample1.jsonl | jq .

# 验证JSONL格式
jq empty /data/qa_output/sample1.jsonl && echo "Valid JSON" || echo "Invalid JSON"

# 统计QA对数量
cat /data/qa_output/sample1.jsonl | wc -l
```

### ✅ 数据质量检查

```python
import json

# 读取JSONL文件
with open('/data/qa_output/sample1.jsonl', 'r', encoding='utf-8') as f:
    qa_pairs = [json.loads(line) for line in f]

# 检查字段完整性
for i, qa in enumerate(qa_pairs[:5]):
    print(f"\n--- QA Pair {i+1} ---")
    print(f"Text Chunk: {qa['text_chunk'][:100]}...")
    print(f"Question: {qa['question']}")
    print(f"Answer: {qa['answer']}")
    
# 统计
print(f"\nTotal QA pairs: {len(qa_pairs)}")
print(f"Average question length: {sum(len(qa['question']) for qa in qa_pairs) / len(qa_pairs):.1f}")
print(f"Average answer length: {sum(len(qa['answer']) for qa in qa_pairs) / len(qa_pairs):.1f}")
```

---

## 常见问题排查

### 问题1: 任务状态一直是 PENDING

**原因**: 后台任务可能没有启动

**解决**:
```python
# 检查API接口中的后台任务是否正确配置
# 查看 app/module/generation/interface/qa_generation.py
# 确保使用了 BackgroundTasks
```

### 问题2: 找不到源文件

**原因**: `t_dm_dataset_files` 中的 `file_path` 不存在

**解决**:
```sql
-- 检查文件路径
SELECT file_path FROM t_dm_dataset_files WHERE dataset_id = 'test-dataset-001';

-- 确保文件存在
-- 在服务器上执行: ls -l /data/test-qa-generation/
```

### 问题3: LLM调用失败

**原因**: API密钥无效或网络问题

**解决**:
```bash
# 测试API连接
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 查看错误日志
tail -f logs/app.log | grep ERROR
```

### 问题4: 外键约束错误

**原因**: 数据集ID不存在

**解决**:
```sql
-- 检查数据集是否存在
SELECT * FROM t_dm_datasets WHERE id = 'test-dataset-001';

-- 如果不存在，先创建数据集
INSERT INTO t_dm_datasets (id, name, dataset_type, status)
VALUES ('test-dataset-001', '测试数据集', 'TEXT', 'ACTIVE');
```

---

## 性能测试

### 小规模测试（推荐先执行）

- **文件数量**: 2个
- **文件大小**: 500字符/文件
- **预期块数**: ~4-6块
- **预期QA对**: ~8-12对
- **预期耗时**: 1-2分钟

### 中等规模测试

- **文件数量**: 10个
- **文件大小**: 5KB/文件
- **预期块数**: ~50-80块
- **预期QA对**: ~100-160对
- **预期耗时**: 10-15分钟

### 大规模测试

- **文件数量**: 100个
- **文件大小**: 10KB/文件
- **预期块数**: ~1000-1500块
- **预期QA对**: ~2000-3000对
- **预期耗时**: 2-3小时

---

## 监控命令

### 实时监控任务进度

```bash
# 每5秒查询一次任务状态
watch -n 5 "mysql -u root -p'password' datamate -e \"
SELECT 
    name,
    status,
    CONCAT(processed_files, '/', total_files) as files,
    CONCAT(processed_chunks, '/', total_chunks) as chunks,
    total_qa_pairs,
    updated_at
FROM t_qa_generation_instances 
WHERE id = 'your-task-id';
\""
```

### 监控QA对生成速度

```bash
# 统计每分钟生成的QA对数量
watch -n 60 "mysql -u root -p'password' datamate -e \"
SELECT 
    DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:00') as minute,
    COUNT(*) as qa_count
FROM t_qa_pairs
WHERE task_id = 'your-task-id'
GROUP BY minute
ORDER BY minute DESC
LIMIT 10;
\""
```

---

## 清理测试数据

```sql
-- 删除测试任务（会级联删除QA对）
DELETE FROM t_qa_generation_instances WHERE name LIKE '测试%';

-- 删除测试数据集（会级联删除文件记录）
DELETE FROM t_dm_datasets WHERE name LIKE '测试%';

-- 清理孤立的QA对（如果有）
DELETE FROM t_qa_pairs 
WHERE task_id NOT IN (SELECT id FROM t_qa_generation_instances);
```

```bash
# 删除测试文件
rm -rf /data/test-qa-generation
rm -rf /data/qa_output
```

---

## 下一步

测试成功后，可以：

1. **集成到前端** - 调用API接口创建和管理QA生成任务
2. **批量处理** - 编写脚本批量处理多个数据集
3. **质量评估** - 添加QA对质量评分和人工审核
4. **性能优化** - 使用批量插入、异步处理等优化性能
5. **监控告警** - 集成监控系统，任务失败时发送告警
