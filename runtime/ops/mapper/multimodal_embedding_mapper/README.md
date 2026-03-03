# 多模态向量嵌入算子

## 功能说明

将图片或视频转换为向量嵌入，支持多模态嵌入模型（如阿里云百炼 multimodal-embedding-v1）并自动存储到 Milvus 向量数据库。

**特性**：
- 自动检测文件类型（图片/视频）
- 自动创建 Milvus Collection（名称使用 `dataset_id`）
- 自动将向量入库到 Milvus
- **所有新生成的输出变量存入 `ext_params` 中**（遵循算子开发规范）

## 参数说明

### 算子配置参数（metadata.yml settings）

| 参数 | 说明 | 是否必填 | 默认值 |
|------|------|----------|--------|
| apiUrl | 多模态嵌入模型的 API 地址 | 是 | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| apiKey | API 密钥 | 是 | - |
| modelName | 嵌入模型名称 | 是 | multimodal-embedding-v1 |
| textPrompt | 可选的文本提示 | 否 | - |
| milvusUri | Milvus 向量数据库地址 | 是 | http://localhost:19530 |

### 运行时参数（sample 顶层字段）

| 参数 | 说明 | 是否必填 | 示例 |
|------|------|----------|------|
| dataset_id | 数据集ID，用于 Milvus collection 名称 | 是（需入库时） | "dataset_123" |

**sample 结构示例**:
```json
{
  "data": "<二进制数据>",
  "fileName": "image.jpg",
  "fileType": "jpg",
  "fileId": "file_001",
  "dataset_id": "dataset_123",
  "ext_params": {}
}
```

## 支持的图片格式

JPEG, PNG, GIF, BMP, WebP, SVG, TIFF

## 支持的视频格式

MP4, AVI, MOV, MKV, WMV, FLV, WebM, M4V, 3GP

## 输出说明

**重要**: 所有新生成的输出变量都存入 `ext_params` 中（遵循算子开发规范，避免不同 sample 字段长度不一致）。

算子执行后，`sample.ext_params` 中会添加以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| embedding | List[float] | 生成的向量嵌入 |
| text | str | 文件元数据描述 |
| embedding_dimension | int | 向量维度 |
| is_image / is_video | bool | 文件类型标记 |
| milvus_inserted | bool | 是否成功入库到 Milvus |
| milvus_doc_id | str | Milvus 文档 ID |
| milvus_collection | str | Milvus collection 名称 |
| embedding_error | str | 错误信息（仅失败时） |

## Milvus Collection 结构

自动创建的 Collection 包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VarChar(36) | 主键，UUID |
| text | VarChar(65535) | 文件描述，支持 BM25 |
| metadata | JSON | 元数据（file_id, file_name, file_type 等） |
| vector | FloatVector | 嵌入向量 |
| sparse | SparseFloatVector | BM25 稀疏向量（自动生成） |

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
      milvusUri: "http://milvus-standalone:19530"
```

## 注意事项

1. 需要配置有效的 API Key
2. API 调用会产生费用，请注意用量
3. 视频文件可能需要较长的处理时间（最长 5 分钟超时）
4. 不支持的文件格式会跳过并记录错误信息到 `ext_params.embedding_error`
5. 需要确保 Milvus 服务可访问
6. **`dataset_id` 在 sample 顶层**（输入参数，保持原有使用方式）
7. **所有新生成的变量都存入 `ext_params` 中**（遵循算子开发规范）
