# DeerFlow Service

## Overview

DeerFlow 是一个 LLM 驱动的服务，用于规划和推理任务，支持多种 LLM 提供商。

## Architecture

```
runtime/deer-flow/
├── conf.yaml       # DeerFlow 配置文件
├── .env            # 环境变量
└── (其他源代码）
```

## Configuration

### 基本配置 (conf.yaml)

```yaml
# 基础模型配置
BASIC_MODEL:
  base_url: https://api.example.com/v1
  model: "model-name"
  api_key: your_api_key
  max_retries: 3
  verify_ssl: false  # 如果使用自签名证书，设为 false

# 推理模型配置（可选）
REASONING_MODEL:
  base_url: https://api.example.com/v1
  model: "reasoning-model-name"
  api_key: your_api_key
  max_retries: 3

# 搜索引擎配置（可选）
SEARCH_ENGINE:
  engine: tavily
  include_domains:
    - example.com
    - trusted-news.com
  exclude_domains:
    - spam-site.com
  search_depth: "advanced"
  include_raw_content: true
  include_images: true
  include_image_descriptions: true
  min_score_threshold: 0.0
  max_content_length_per_page: 4000
```

### 支持的 LLM 提供商

#### OpenAI
```yaml
BASIC_MODEL:
  base_url: https://api.openai.com/v1
  model: "gpt-4"
  api_key: sk-...
```

#### Ollama (本地部署）
```yaml
BASIC_MODEL:
  base_url: "http://localhost:11434/v1"
  model: "qwen2:7b"
  api_key: "ollama"
  verify_ssl: false
```

#### Google AI Studio
```yaml
BASIC_MODEL:
  platform: "google_aistudio"
  model: "gemini-2.5-flash"
  api_key: your_gemini_api_key
```

#### 华为云
```yaml
BASIC_MODEL:
  base_url: https://ark.cn-beijing.volces.com/api/v3
  model: "doubao-1-5-pro-32k-250115"
  api_key: your_api_key
```

## Quick Start

### Prerequisites
- Python 3.8+
- LLM API Key 或本地 LLM

### 配置
1. 复制 `conf.yaml.example` 为 `conf.yaml`
2. 配置 LLM 提供商和 API Key
3. （可选）配置推理模型和搜索引擎

### 运行
```bash
cd runtime/deer-flow
python -m deerflow
```

## Usage

### 基本规划
```python
from deerflow import DeerFlow

flow = DeerFlow()
result = flow.plan(
    task="设计一个数据处理流程",
    context="需要处理CSV文件，进行数据清洗和转换"
)
print(result)
```

### 推理任务
```python
from deerflow import DeerFlow

flow = DeerFlow()
result = flow.reason(
    task="分析数据质量",
    context="数据包含缺失值和异常值"
)
print(result)
```

## Development

### 添加新的 LLM 提供商
1. 在 `conf.yaml` 添加新的模型配置
2. 实现对应的 API 调用逻辑
3. 测试连接和推理

### 自定义提示词模板
1. 创建提示词模板文件
2. 在 `conf.yaml` 引用模板
3. 测试提示词效果

## Documentation

- [DeerFlow 官方文档](https://github.com/ModelEngine-Group/DeerFlow)

## Related Links

- [Runtime README](../README.md)
