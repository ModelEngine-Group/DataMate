# DeerFlow Service

## Overview

DeerFlow is an LLM-driven service for planning and reasoning tasks, supporting multiple LLM providers.

## Architecture

```
runtime/deer-flow/
├── conf.yaml       # DeerFlow configuration file
├── .env            # Environment variables
└── (other source code)
```

## Configuration

### Basic Configuration (conf.yaml)

```yaml
# Basic model configuration
BASIC_MODEL:
  base_url: https://api.example.com/v1
  model: "model-name"
  api_key: your_api_key
  max_retries: 3
  verify_ssl: false  # Set to false if using self-signed certificates

# Reasoning model configuration (optional)
REASONING_MODEL:
  base_url: https://api.example.com/v1
  model: "reasoning-model-name"
  api_key: your_api_key
  max_retries: 3

# Search engine configuration (optional)
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

## Supported LLM Providers

#### OpenAI
```yaml
BASIC_MODEL:
  base_url: https://api.openai.com/v1
  model: "gpt-4"
  api_key: sk-...
```

#### Ollama (Local Deployment)
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

## Development

### Adding a New LLM Provider
1. Add new model configuration in `conf.yaml`
2. Implement corresponding API call logic
3. Test connection and inference

### Customizing Prompt Templates
1. Create a prompt template file
2. Reference the template in `conf.yaml`
3. Test prompt effectiveness

## Documentation

- [DeerFlow Official Documentation](https://github.com/ModelEngine-Group/DeerFlow)

## Related Links

- [Runtime README](../README.md)
