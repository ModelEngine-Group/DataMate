# QA生成模块 - 新版本使用指南

## 新功能说明

### ✨ 版本更新（v2.0）

1. **文件级别控制** - 不再输入整个 dataset_id，而是输入 file_ids 列表
2. **Alpaca格式输出** - JSONL格式改为Alpaca标准格式
3. **自定义提示词** - 支持 extra_prompt，插入到LLM Prompt中
4. **多格式支持** - 支持 .txt, .md, .json 格式文件

---

## API 使用示例

### 1. 基础请求示例

```bash
curl -X POST "http://localhost:8000/api/generation/qa-generation" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "骆驼祥子QA生成",
    "description": "从选定的章节生成QA对",
    "sourceFileIds": [
      "file-uuid-001",
      "file-uuid-002",
      "file-uuid-003"
    ],
    "textSplitConfig": {
      "max_characters": 50000,
      "chunk_size": 800,
      "chunk_overlap": 200
    },
    "qaGenerationConfig": {
      "max_questions": 2,
      "temperature": 0.3,
      "model": "gpt-5-nano"
    },
    "llmApiKey": "sk-oWWhBK0Fagn3j4Mv0pLDiOF6fkJnjVKXtTwlye7oXG1uPc6m",
    "llmBaseUrl": "https://api.chatanywhere.tech/v1"
  }'
```

### 2. 带自定义提示词

```bash
curl -X POST "http://localhost:8000/api/generation/qa-generation" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "技术文档QA生成",
    "sourceFileIds": ["file-uuid-001", "file-uuid-002"],
    "extraPrompt": "请生成针对技术新手的简单问答，避免使用过于专业的术语",
    "textSplitConfig": {
      "chunk_size": 1000,
      "chunk_overlap": 200
    },
    "qaGenerationConfig": {
      "max_questions": 2,
      "temperature": 0.5,
      "model": "gpt-4"
    },
    "llmApiKey": "sk-xxx",
    "llmBaseUrl": "https://api.openai.com/v1"
  }'
```

### 3. 处理 JSON 格式文件

```bash
curl -X POST "http://localhost:8000/api/generation/qa-generation" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "JSON数据QA生成",
    "description": "从JSON文件中提取文本并生成QA",
    "sourceFileIds": [
      "json-file-uuid-001"
    ],
    "textSplitConfig": {
      "chunk_size": 600,
      "chunk_overlap": 150
    },
    "qaGenerationConfig": {
      "max_questions": 3,
      "temperature": 0.3,
      "model": "gpt-3.5-turbo"
    },
    "llmApiKey": "sk-xxx",
    "llmBaseUrl": "https://api.openai.com/v1"
  }'
```

---

## 获取 File IDs

### 方法1: 查询数据库

```sql
-- 查看某个数据集的所有文件
SELECT 
    id,
    file_name,
    file_type,
    file_size,
    created_at
FROM t_dm_dataset_files
WHERE dataset_id = 'your-dataset-id'
  AND status = 'ACTIVE'
  AND file_name LIKE '%.txt'  -- 或 %.md, %.json
ORDER BY created_at DESC;

-- 获取特定文件的ID
SELECT id, file_name 
FROM t_dm_dataset_files 
WHERE file_name IN ('chapter1.txt', 'chapter2.txt', 'chapter3.txt');
```

### 方法2: 通过数据管理API

```bash
# 获取数据集的文件列表
curl "http://localhost:8000/api/data-management/datasets/{dataset_id}/files"
```

---

## Alpaca 格式说明

### 旧格式 (v1.0)
```json
{
  "text_chunk": "祥子是一个人力车夫...",
  "question": "祥子的职业是什么？",
  "answer": "祥子的职业是人力车夫"
}
```

### 新格式 (v2.0 - Alpaca)
```json
{
  "instruction": "祥子的职业是什么？",
  "input": "祥子是一个人力车夫...",
  "output": "祥子的职业是人力车夫"
}
```

### Alpaca 格式说明

- **instruction**: 问题/指令
- **input**: 上下文文本块
- **output**: 答案

这是标准的指令微调数据格式，可以直接用于训练大模型。

---

## JSONL 文件位置

生成的 JSONL 文件保存在：

```
runtime/datamate-python/app/module/generation/generated_data/{task_id}/
├── file1.jsonl
├── file2.jsonl
└── file3.jsonl
```

每个源文件生成一个对应的 JSONL 文件：
- `chapter1.txt` → `chapter1.jsonl`
- `document.md` → `document.jsonl`
- `data.json` → `data.jsonl`

---

## Extra Prompt 使用建议

### 1. 控制问题类型

```json
{
  "extraPrompt": "请生成事实性问题，不要生成推理或假设性问题"
}
```

### 2. 指定目标受众

```json
{
  "extraPrompt": "问题应该适合小学生理解，使用简单的语言"
}
```

### 3. 控制答案长度

```json
{
  "extraPrompt": "每个答案控制在50字以内，简洁明了"
}
```

### 4. 指定问题风格

```json
{
  "extraPrompt": "生成开放式问题，鼓励深入思考"
}
```

### 5. 针对特定领域

```json
{
  "extraPrompt": "聚焦于技术实现细节，忽略背景介绍"
}
```

---

## 文件格式支持

### .txt 文件
- 直接读取全文
- 适合纯文本内容

### .md 文件 (Markdown)
- 直接读取全文（包含Markdown标记）
- Markdown格式会保留在文本块中
- 适合技术文档、博客文章

### .json 文件
- 递归提取所有字符串值
- 自动忽略数字、布尔值等非文本数据
- 适合结构化数据

**示例 JSON 处理：**

输入文件 `data.json`:
```json
{
  "title": "机器学习入门",
  "content": "机器学习是人工智能的一个分支...",
  "author": {
    "name": "张三",
    "bio": "资深AI研究员"
  },
  "tags": ["AI", "ML", "教程"]
}
```

提取的文本:
```
机器学习入门

机器学习是人工智能的一个分支...

张三

资深AI研究员

AI

ML

教程
```

---

## 完整工作流程

### 步骤1: 准备数据

```sql
-- 上传文件到 t_dm_dataset_files
INSERT INTO t_dm_dataset_files (id, dataset_id, file_name, file_path, file_type, status)
VALUES 
  ('file-001', 'ds-001', 'chapter1.txt', '/data/ch1.txt', 'txt', 'ACTIVE'),
  ('file-002', 'ds-001', 'chapter2.md', '/data/ch2.md', 'md', 'ACTIVE'),
  ('file-003', 'ds-001', 'data.json', '/data/data.json', 'json', 'ACTIVE');
```

### 步骤2: 创建QA生成任务

```bash
curl -X POST "http://localhost:8000/api/generation/qa-generation" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "多格式文件QA生成",
    "sourceFileIds": ["file-001", "file-002", "file-003"],
    "extraPrompt": "生成适合技术学习的问答对",
    "textSplitConfig": {"chunk_size": 800, "chunk_overlap": 200},
    "qaGenerationConfig": {"max_questions": 3, "temperature": 0.3, "model": "gpt-3.5-turbo"},
    "llmApiKey": "sk-xxx",
    "llmBaseUrl": "https://api.openai.com/v1"
  }'
```

### 步骤3: 监控任务进度

```bash
# 获取任务状态
curl "http://localhost:8000/api/generation/qa-generation/{task_id}"
```

### 步骤4: 查看生成结果

```bash
# 查看 JSONL 文件
cat runtime/datamate-python/app/module/generation/generated_data/{task_id}/chapter1.jsonl | jq .

# 查看前3条
head -n 3 chapter1.jsonl | jq .
```

### 步骤5: 验证数据

```sql
-- 查看生成的QA对
SELECT 
    source_file_name,
    question,
    answer,
    chunk_index
FROM t_qa_pairs
WHERE task_id = 'your-task-id'
ORDER BY source_file_name, chunk_index
LIMIT 10;

-- 查看目标数据集文件
SELECT 
    f.file_name,
    f.file_path,
    f.file_size,
    d.name as dataset_name
FROM t_dm_dataset_files f
JOIN t_dm_datasets d ON f.dataset_id = d.id
JOIN t_qa_generation_instances qi ON d.id = qi.target_dataset_id
WHERE qi.id = 'your-task-id';
```

---

## 常见问题

### Q1: File ID 从哪里获取？
A: File ID 是 `t_dm_dataset_files` 表中的主键 `id` 字段。可以通过查询数据库或数据管理API获取。

### Q2: 可以混合不同格式的文件吗？
A: 可以！sourceFileIds 可以包含 .txt, .md, .json 等不同格式的文件ID，系统会自动识别并处理。

### Q3: Extra Prompt 有长度限制吗？
A: 最大2000字符。建议保持简洁，50-200字为佳。

### Q4: JSON文件中的嵌套结构会被保留吗？
A: 不会。系统递归提取所有字符串值并平铺拼接，结构信息会丢失。

### Q5: JSONL文件会自动上传到数据库吗？
A: 会。生成的JSONL文件会自动记录到 `t_dm_dataset_files` 表，并关联到目标数据集。

### Q6: 如何只处理部分文件？
A: 这正是新版本的核心功能！只需在 sourceFileIds 中指定你想处理的文件ID即可。

---

## 示例场景

### 场景1: 从大型文档集中选择性生成QA

```python
# 假设有100个文件，只想处理其中5个
file_ids_to_process = [
    "f1a2b3c4-...",  # 最重要的章节
    "f5d6e7f8-...",
    "f9g0h1i2-...",
    "f3j4k5l6-...",
    "f7m8n9o0-..."
]

# 创建任务
{
  "name": "重点章节QA生成",
  "sourceFileIds": file_ids_to_process,
  ...
}
```

### 场景2: 技术文档QA生成（带自定义提示词）

```json
{
  "name": "API文档QA生成",
  "sourceFileIds": ["api-doc-1", "api-doc-2"],
  "extraPrompt": "生成针对API使用方法的实用问答，包含代码示例的说明",
  "qaGenerationConfig": {
    "max_questions": 5,
    "temperature": 0.2,
    "model": "gpt-4"
  }
}
```

### 场景3: 多语言混合处理

```json
{
  "name": "多语言文档QA",
  "sourceFileIds": [
    "english-doc-001",    // .txt
    "chinese-doc-002",    // .md
    "bilingual-data-003"  // .json
  ],
  "extraPrompt": "保持原文语言生成问答，不要翻译",
  ...
}
```

---

## 性能建议

1. **分批处理**: 如果有很多文件，建议分多个任务处理（每次10-20个文件）
2. **合理切片**: chunk_size 建议 500-1000，太小会导致上下文不足，太大会影响QA质量
3. **监控进度**: 大任务建议定期查询任务状态
4. **清理数据**: 完成后可以删除中间数据（t_qa_pairs），保留JSONL即可

---

## 下一步

生成的 Alpaca 格式 JSONL 文件可以直接用于：
- 大模型指令微调
- RAG系统构建
- 知识库问答
- 评测数据集构建
