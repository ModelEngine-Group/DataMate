# DeerFlow 服务

## 概述

DeerFlow 是一个 LLM 驱动的服务，用于规划和推理任务，支持多种 LLM 提供商。

## 架构

```
runtime/deer-flow/
├── conf.yaml       # DeerFlow 配置文件
├── .env            # 环境变量
└── (其他源代码）
```

## 配置

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

## 支的 LLM 提供商

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

## 开发

### 添加新的 LLM 提供商
1. 在 `conf.yaml` 添加新的模型配置
2. 实现对应的 API 调用逻辑
3. 测试连接和推理

### 自定义提示词模板
1. 创建提示词模板文件
2. 在 `conf.yaml` 引用模板
3. 测试提示词效果

## 文档

- [DeerFlow 官方文档](https://github.com/ModelEngine-Group/DeerFlow)

## 相关链接

- [运行时 README](../README.md)
