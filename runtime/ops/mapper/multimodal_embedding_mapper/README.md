# 多模态向量嵌入算子

## 功能说明

将图片或视频转换为向量嵌入，支持多模态嵌入模型（如阿里云百炼 multimodal-embedding-v1）。

**自动检测文件类型**，无需手动指定是图片还是视频。

## 参数说明

| 参数 | 说明 | 是否必填 | 默认值 |
|------|------|----------|--------|
| apiUrl | 多模态嵌入模型的 API 地址 | 是 | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| apiKey | API 密钥 | 是 | - |
| modelName | 嵌入模型名称 | 是 | multimodal-embedding-v1 |
| textPrompt | 可选的文本提示 | 否 | - |

## 支持的图片格式

JPEG, PNG, GIF, BMP, WebP, SVG, TIFF

## 支持的视频格式

MP4, AVI, MOV, MKV, WMV, FLV, WebM, M4V, 3GP

## 输出说明

算子执行后，sample 中会添加以下字段：

- `embedding`: 生成的向量嵌入（float 列表）
- `text`: 文件元数据描述
- `embedding_dimension`: 向量维度
- `is_image`: 标记为图片文件（仅图片）
- `is_video`: 标记为视频文件（仅视频）

## 使用示例

```yaml
# 在清洗流水线中使用
operators:
  - name: multimodal_embedding_mapper
    type: MultimodalEmbeddingMapper
    params:
      apiUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1"
      apiKey: "${DASHSCOPE_API_KEY}"
      modelName: "multimodal-embedding-v1"
      textPrompt: ""
```

## 注意事项

1. 需要配置有效的 API Key
2. API 调用会产生费用，请注意用量
3. 视频文件可能需要较长的处理时间（最长 5 分钟超时）
4. 不支持的文件格式会跳过并记录错误信息
