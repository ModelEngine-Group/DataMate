# 使用本地文件的示例

## API 调用示例

### 使用本地 .txt 文件

```bash
curl -X POST "http://localhost:8000/api/generation/qa-generation" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "骆驼祥子QA生成",
    "description": "从本地txt文件生成问答对",
    "sourceFilePath": "C:/Users/meta/Desktop/Datamate/DataMate/runtime/datamate-python/app/module/generation/骆驼祥子_节选.txt",
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
    "llmApiKey": "sk-oWWhBK0Fagn3j4Mv0pLDiOF6fkJnjVKXtTwlye7oXG1uPc6m",
    "llmBaseUrl": "https://api.chatanywhere.tech/v1"
  }'
```

### Python 客户端示例

```python
import requests

# 使用本地文件
response = requests.post(
    "http://localhost:8000/api/generation/qa-generation",
    json={
        "name": "本地文件QA生成",
        "sourceFilePath": "C:/path/to/your/file.txt",
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
    }
)

if response.status_code == 200:
    data = response.json()
    task_id = data["data"]["id"]
    print(f"任务创建成功! ID: {task_id}")
    
    # 轮询任务状态
    import time
    while True:
        status_response = requests.get(
            f"http://localhost:8000/api/generation/qa-generation/{task_id}"
        )
        task_data = status_response.json()["data"]
        status = task_data["status"]
        
        print(f"状态: {status}")
        print(f"进度: {task_data['processed_chunks']}/{task_data['total_chunks']}")
        
        if status in ["COMPLETED", "FAILED"]:
            break
        
        time.sleep(5)
else:
    print(f"错误: {response.text}")
```

## 支持的文件格式

- ✅ `.txt` - 纯文本文件
- ✅ `.md` - Markdown文件
- ❌ 其他格式暂不支持

## 注意事项

1. **文件路径**: 
   - Windows: 使用 `C:/path/to/file.txt` 或 `C:\\path\\to\\file.txt`
   - Linux/Mac: 使用 `/path/to/file.txt`

2. **文件编码**: 
   - 必须是 UTF-8 编码
   - 如果有乱码，请先转换文件编码

3. **文件大小**: 
   - 建议单个文件不超过 10MB
   - 过大的文件会影响处理时间

4. **临时数据集**: 
   - 使用本地文件时，系统会自动创建一个临时数据集记录
   - 这个记录用于追踪任务，不影响实际文件

## 对比两种方式

| 特性 | sourceDatasetId | sourceFilePath |
|------|-----------------|----------------|
| 数据来源 | 数据库中的数据集 | 本地文件系统 |
| 前置要求 | 需要先创建数据集 | 只需要文件存在 |
| 使用场景 | 生产环境，批量处理 | 测试，快速验证 |
| 文件格式 | 数据集格式 | .txt, .md |
| 推荐程度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

## 完整工作流示例

```python
import requests
import time
import json

def create_qa_task_from_file(file_path: str, api_key: str):
    """从本地文件创建QA生成任务"""
    
    # 1. 创建任务
    print(f"创建任务，使用文件: {file_path}")
    response = requests.post(
        "http://localhost:8000/api/generation/qa-generation",
        json={
            "name": f"QA生成-{file_path.split('/')[-1]}",
            "description": "自动生成的QA任务",
            "sourceFilePath": file_path,
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
            "llmApiKey": api_key,
            "llmBaseUrl": "https://api.chatanywhere.tech/v1"
        }
    )
    
    if response.status_code != 200:
        print(f"创建失败: {response.text}")
        return None
    
    task_id = response.json()["data"]["id"]
    print(f"✓ 任务创建成功! ID: {task_id}")
    
    # 2. 监控进度
    print("\n监控任务进度...")
    while True:
        response = requests.get(
            f"http://localhost:8000/api/generation/qa-generation/{task_id}"
        )
        data = response.json()["data"]
        
        status = data["status"]
        processed = data.get("processed_chunks", 0)
        total = data.get("total_chunks", 0)
        qa_pairs = data.get("total_qa_pairs", 0)
        
        print(f"[{status}] 进度: {processed}/{total} 块, 已生成 {qa_pairs} 个QA对")
        
        if status == "COMPLETED":
            print("\n✓ 任务完成!")
            print(f"总共生成了 {qa_pairs} 个问答对")
            print(f"目标数据集ID: {data['target_dataset_id']}")
            break
        elif status == "FAILED":
            print(f"\n✗ 任务失败: {data.get('error_message')}")
            break
        
        time.sleep(5)
    
    return task_id

# 使用示例
if __name__ == "__main__":
    file_path = "C:/Users/meta/Desktop/骆驼祥子_节选.txt"
    api_key = "sk-oWWhBK0Fagn3j4Mv0pLDiOF6fkJnjVKXtTwlye7oXG1uPc6m"
    
    task_id = create_qa_task_from_file(file_path, api_key)
    
    if task_id:
        print(f"\n任务完成! 可以查询结果:")
        print(f"http://localhost:8000/api/generation/qa-generation/{task_id}")
```

## 故障排查

### 文件不存在错误

```json
{
  "success": false,
  "message": "文件不存在: C:/path/to/file.txt"
}
```

**解决方案**: 检查文件路径是否正确，文件是否存在

### 文件格式不支持

```json
{
  "success": false,
  "message": "仅支持 .txt 或 .md 文件，当前: .pdf"
}
```

**解决方案**: 将文件转换为 .txt 或 .md 格式

### 文件编码错误

```json
{
  "success": false,
  "message": "Failed to read file: 'utf-8' codec can't decode..."
}
```

**解决方案**: 将文件转换为 UTF-8 编码
