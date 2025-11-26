# QA对生成完整数据流程文档

## 数据流程图

```
┌────────────────────────────────────────────────────────────────┐
│  Step 1: 读取源数据                                             │
│  从 t_dm_dataset_files 读取源数据集的所有 .txt 文件             │
└──────────────────────────┬─────────────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────────────┐
│  Step 2: 文本切片与QA生成                                       │
│  - 对每个 .txt 文件进行文本切片                                 │
│  - 为每个文本块调用 LLM 生成问答对                              │
└──────────────────────────┬─────────────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────────────┐
│  Step 3: 存储QA对到数据库                                       │
│  将生成的QA对存入 t_qa_pairs 表                                 │
│  三列结构: text_chunk | question | answer                       │
└──────────────────────────┬─────────────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────────────┐
│  Step 4: 导出JSONL文件                                          │
│  从 t_qa_pairs 读取数据，按源文件导出为 .jsonl                  │
│  abc.txt → abc.jsonl                                            │
└──────────────────────────┬─────────────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────────────┐
│  Step 5: 保存到目标数据集                                       │
│  将 .jsonl 文件信息保存到 t_dm_dataset_files (目标数据集)       │
└────────────────────────────────────────────────────────────────┘
```

## 涉及的数据库表

### 1. t_dm_datasets (数据集表)
- 存储源数据集和目标数据集的元信息

### 2. t_dm_dataset_files (数据集文件表)
- **输入**: 存储源数据集的 .txt 文件信息
- **输出**: 存储生成的 .jsonl 文件信息

### 3. t_qa_generation_instances (QA生成任务表)
- 存储任务的配置、状态和进度信息

### 4. t_qa_pairs (QA对数据表) ⭐ 核心表
- 存储所有生成的问答对
- 结构:
  ```sql
  - text_chunk: 文本块内容
  - question: 问题
  - answer: 答案
  - source_file_id: 源文件ID
  - chunk_index: 块索引
  ```

## 详细流程说明

### Step 1: 读取源数据

```python
# 从 t_dm_dataset_files 查询源数据集的所有 .txt 文件
SELECT * FROM t_dm_dataset_files 
WHERE dataset_id = 'source_dataset_id' 
  AND file_type IN ('txt', 'TXT', '.txt')
  AND status = 'ACTIVE';
```

**示例数据**:
```
dataset_id: ds_001
files:
  - id: file_001, name: "chapter1.txt", path: "/data/text/chapter1.txt"
  - id: file_002, name: "chapter2.txt", path: "/data/text/chapter2.txt"
  - id: file_003, name: "chapter3.txt", path: "/data/text/chapter3.txt"
```

### Step 2: 文本切片与QA生成

对每个文件:

1. **读取文件内容**
   ```python
   with open(file.file_path, 'r', encoding='utf-8') as f:
       text_content = f.read()
   ```

2. **文本切片**
   ```python
   splitter = TextSplitter(
       max_characters=50000,
       chunk_size=800,
       chunk_overlap=200
   )
   chunks = splitter.split_text(text_content)
   # 结果: ["chunk1...", "chunk2...", "chunk3..."]
   ```

3. **生成QA对**
   ```python
   for chunk_index, chunk in enumerate(chunks):
       qa_pairs = llm.generate_qa(chunk, max_questions=3)
       # 结果: [
       #   {"question": "问题1", "answer": "答案1"},
       #   {"question": "问题2", "answer": "答案2"}
       # ]
   ```

### Step 3: 存储QA对到数据库

对每个QA对，插入到 `t_qa_pairs` 表:

```sql
INSERT INTO t_qa_pairs (
    id,
    task_id,
    source_file_id,
    source_file_name,
    chunk_index,
    text_chunk,
    question,
    answer,
    created_at
) VALUES (
    'qa_001',
    'task_123',
    'file_001',
    'chapter1.txt',
    0,
    '祥子是一个人力车夫...',
    '祥子的职业是什么？',
    '祥子的职业是人力车夫。',
    NOW()
);
```

**存储结构示例**:
```
task_id: task_123
  └─ source_file: chapter1.txt (file_001)
       ├─ chunk_0
       │    ├─ text_chunk: "祥子是一个人力车夫..."
       │    ├─ QA1: Q="祥子的职业是什么？" A="人力车夫"
       │    └─ QA2: Q="祥子来自哪里？" A="农村"
       ├─ chunk_1
       │    ├─ text_chunk: "他努力工作..."
       │    └─ QA1: Q="祥子如何买车？" A="通过努力工作攒钱"
       └─ ...
```

### Step 4: 导出JSONL文件

对每个源文件，从 `t_qa_pairs` 查询其所有QA对并导出:

```python
# 查询该文件的所有QA对
qa_pairs = db.query(QAPair).filter(
    QAPair.task_id == task_id,
    QAPair.source_file_id == source_file_id
).order_by(QAPair.chunk_index).all()

# 导出为JSONL格式
# chapter1.txt → chapter1.jsonl
with open("chapter1.jsonl", "w", encoding="utf-8") as f:
    for qa in qa_pairs:
        record = {
            "text_chunk": qa.text_chunk,
            "question": qa.question,
            "answer": qa.answer
        }
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
```

**JSONL文件内容示例** (`chapter1.jsonl`):
```jsonl
{"text_chunk": "祥子是一个人力车夫，他来自农村...", "question": "祥子的职业是什么？", "answer": "祥子的职业是人力车夫。"}
{"text_chunk": "祥子是一个人力车夫，他来自农村...", "question": "祥子来自哪里？", "answer": "祥子来自农村。"}
{"text_chunk": "他努力工作，希望能买一辆自己的车...", "question": "祥子如何买车？", "answer": "通过努力工作攒钱。"}
```

### Step 5: 保存到目标数据集

将生成的 JSONL 文件信息保存到 `t_dm_dataset_files`:

```sql
INSERT INTO t_dm_dataset_files (
    id,
    dataset_id,
    file_name,
    file_path,
    file_type,
    file_size,
    status,
    upload_time,
    created_at
) VALUES (
    'new_file_001',
    'target_dataset_id',
    'chapter1.jsonl',
    '/data/qa_output/task_123/chapter1.jsonl',
    'jsonl',
    12345,
    'ACTIVE',
    NOW(),
    NOW()
);
```

**最终目标数据集结构**:
```
target_dataset_id: ds_002
  name: "骆驼祥子QA数据集_QA_JSONL"
  type: "QA"
  format: "JSONL"
  files:
    - chapter1.jsonl  (对应源文件 chapter1.txt)
    - chapter2.jsonl  (对应源文件 chapter2.txt)
    - chapter3.jsonl  (对应源文件 chapter3.txt)
```

## 数据映射关系

### 源数据集 → 目标数据集

```
源数据集 (TEXT类型):
  └─ chapter1.txt
  └─ chapter2.txt
  └─ chapter3.txt

      ⬇ QA Generation

目标数据集 (QA类型):
  └─ chapter1.jsonl
  └─ chapter2.jsonl
  └─ chapter3.jsonl
```

### 文件内容映射

```
chapter1.txt (纯文本):
----------------------------
祥子是一个人力车夫，他来自农村，
来到北京后，决心靠自己的劳动买一辆车...

      ⬇ 切片 + QA生成

chapter1.jsonl (QA对):
----------------------------
{"text_chunk": "祥子是一个...", "question": "...", "answer": "..."}
{"text_chunk": "祥子是一个...", "question": "...", "answer": "..."}
{"text_chunk": "他努力工作...", "question": "...", "answer": "..."}
...
```

## API 使用示例

### 创建任务

```bash
curl -X POST "http://localhost:8000/api/generation/qa-generation" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "骆驼祥子QA生成",
    "description": "从骆驼祥子文本生成问答对",
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

### 查询进度

```bash
curl "http://localhost:8000/api/generation/qa-generation/{task_id}"
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": "task_123",
    "name": "骆驼祥子QA生成",
    "status": "RUNNING",
    "total_files": 3,
    "processed_files": 1,
    "total_chunks": 150,
    "processed_chunks": 50,
    "total_qa_pairs": 120
  }
}
```

## 进度追踪

任务执行过程中，实时更新以下字段:

- `total_files`: 源数据集中的 .txt 文件总数
- `processed_files`: 已完成处理的文件数
- `total_chunks`: 所有文件切片后的总块数
- `processed_chunks`: 已完成QA生成的块数
- `total_qa_pairs`: 生成的QA对总数

**进度计算**:
```
文件处理进度 = processed_files / total_files * 100%
块处理进度 = processed_chunks / total_chunks * 100%
```

## 错误处理

- 如果某个文件处理失败，记录错误但继续处理其他文件
- 任务失败时，`status` 更新为 `FAILED`，`error_message` 记录错误信息
- 已生成的QA对仍然保留在 `t_qa_pairs` 表中

## 数据清理

删除任务时，自动清理:
1. `t_qa_generation_instances` 中的任务记录
2. `t_qa_pairs` 中该任务的所有QA对记录

注意: 不自动删除生成的 JSONL 文件和目标数据集，需要手动管理。

## 性能优化建议

1. **批量处理**: 使用批量插入减少数据库IO
2. **并发控制**: 限制同时执行的任务数量
3. **缓存策略**: 缓存LLM响应避免重复调用
4. **分页导出**: 大文件分批导出JSONL避免内存溢出

## 扩展功能

未来可以添加:
- QA对质量评估
- 人工审核和修正
- QA对去重和合并
- 多语言支持
- 自定义QA生成模板
