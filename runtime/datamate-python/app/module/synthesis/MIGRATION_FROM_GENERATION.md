# QA生成模块迁移到Synthesis总结

## 迁移日期
2025年11月25日

## 迁移原因
将 QA 生成功能作为数据合成 (synthesis) 的一个子功能模块,与 ratio-task 并列,统一管理数据生成相关功能。

## 迁移内容

### 1. 文件迁移
```
generation/ → synthesis/
├── schema/qa_generation.py → synthesis/schema/qa_generation.py
├── service/qa_generation.py → synthesis/service/qa_generation.py
├── service/text_splitter.py → synthesis/service/text_splitter.py
├── interface/qa_generation.py → synthesis/interface/qa_generation.py
└── generated_data/ → synthesis/generated_data/
```

### 2. 导入路径更新
所有模块内部导入路径已更新:
- `app.module.generation` → `app.module.synthesis`

具体文件:
- `synthesis/service/qa_generation.py`: 更新 TextSplitter 导入
- `synthesis/interface/qa_generation.py`: 更新 schema 和 service 导入
- `app/module/__init__.py`: 更新路由导入和挂载路径

### 3. API 路径变更

#### 旧路径 (已弃用)
```
POST /api/generation/qa-generation
GET  /api/generation/qa-generation
GET  /api/generation/qa-generation/{id}
DELETE /api/generation/qa-generation/{id}
```

#### 新路径 (当前)
```
POST /api/synthesis/qa-generation
GET  /api/synthesis/qa-generation
GET  /api/synthesis/qa-generation/{id}
DELETE /api/synthesis/qa-generation/{id}
```

### 4. 标签变更
- 旧标签: `generation/qa-generation`
- 新标签: `synthesis/qa-generation`

## 功能保持
- ✅ 所有 QA 生成功能保持不变
- ✅ Alpaca JSONL 格式输出
- ✅ 多文件格式支持 (.txt, .md, .json)
- ✅ Extra prompt 自定义提示词
- ✅ 文件级别控制 (file_ids)
- ✅ 生成数据保存在 `synthesis/generated_data/`

## 数据库
无需修改,所有数据库表保持不变:
- `t_qa_generation_instances`
- `t_qa_pairs`
- 数据库模型位于 `app/db/models/qa_generation.py` (未迁移)

## 测试建议
1. 启动服务验证无导入错误
2. 使用新 API 路径测试 QA 生成功能
3. 验证 generated_data 文件正确保存到 synthesis 目录

## 示例 API 调用 (更新后)

```bash
curl -X POST "http://localhost:8000/api/synthesis/qa-generation" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "骆驼祥子QA生成",
    "description": "从选定的章节生成QA对",
    "sourceFileIds": ["file-uuid-001", "file-uuid-002"],
    "extraPrompt": "请生成适合中学生理解的问答",
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
    "llmApiKey": "sk-xxx",
    "llmBaseUrl": "https://api.openai.com/v1"
  }'
```

## 后续工作
1. ✅ 验证服务启动成功
2. ✅ 测试新 API 路径
3. 🔄 更新前端调用 (如果有)
4. 🔄 更新 API 文档
5. 🔄 删除旧的 generation 文件夹 (保留 Markdown 文档)

## 注意事项
- 旧的 `/api/generation/qa-generation` 路径已不可用
- 需要更新所有客户端调用到新路径
- 文档位于 `generation/Markdown/` 可移动到 `synthesis/` 或单独保存
