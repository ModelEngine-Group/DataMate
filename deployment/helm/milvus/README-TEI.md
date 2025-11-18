# Text Embeddings Inference (TEI) Integration Guide

This document describes how to use Text Embeddings Inference (TEI) service with Milvus Helm Chart, and how to integrate TEI with Milvus. TEI is an open-source project developed by Hugging Face, available at [https://github.com/huggingface/text-embeddings-inference](https://github.com/huggingface/text-embeddings-inference).

## Overview

Text Embeddings Inference (TEI) is a high-performance text embedding model inference service that converts text into vector representations. Milvus is a vector database that can store and retrieve these vectors. By combining the two, you can build powerful semantic search and retrieval systems.

## Deployment Methods

This guide provides two ways to use TEI:
1. Deploy TEI service directly through the Milvus Helm Chart
2. Use external TEI service with Milvus integration

## Deploy TEI through Milvus Helm Chart

### Basic Configuration

Enable TEI service in `values.yaml`:

```yaml
tei:
  enabled: true
  modelId: "BAAI/bge-large-en-v1.5"  # Specify the model to use
```

This is the simplest configuration, just specify `enabled: true` and the desired `modelId`.

### Complete Configuration Options

```yaml
tei:
  enabled: true                        # Enable TEI service
  name: text-embeddings-inference      # Service name
  replicas: 1                          # Number of TEI replicas
  image:
    repository: ghcr.io/huggingface/text-embeddings-inference  # Image repository
    tag: cpu-1.6                       # Image tag (CPU version)
    pullPolicy: IfNotPresent           # Image pull policy
  service:
    type: ClusterIP                    # Service type
    port: 8080                         # Service port
    annotations: {}                    # Service annotations
    labels: {}                         # Service labels
  resources:                           # Resource configuration
    requests:
      cpu: "4"                         # CPU request
      memory: "8Gi"                    # Memory request
    limits:
      cpu: "8"                         # CPU limit
      memory: "16Gi"                   # Memory limit
  persistence:                         # Persistence storage configuration
    enabled: true                      # Enable persistence storage
    mountPath: "/data"                 # Mount path
    annotations: {}                    # Storage annotations
    persistentVolumeClaim:             # PVC configuration
      existingClaim: ""                # Use existing PVC
      storageClass:                    # Storage class
      accessModes: ReadWriteOnce       # Access modes
      size: 50Gi                       # Storage size
      subPath: ""                      # Sub path
  modelId: "BAAI/bge-large-en-v1.5"    # Model ID
  extraArgs: []                        # Additional command line arguments for TEI, such as "--max-batch-tokens=16384", "--max-client-batch-size=32", "--max-concurrent-requests=128", etc.
  nodeSelector: {}                     # Node selector
  affinity: {}                         # Affinity configuration
  tolerations: []                      # Tolerations
  topologySpreadConstraints: []        # Topology spread constraints
  extraEnv: []                         # Additional environment variables
```

### Using GPU Acceleration

If you have GPU resources, you can use the GPU version of the TEI image to accelerate inference:

```yaml
tei:
  enabled: true
  modelId: "BAAI/bge-large-en-v1.5"
  image:
    repository: ghcr.io/huggingface/text-embeddings-inference
    tag: 1.6  # GPU version
  resources:
    limits:
      nvidia.com/gpu: 1  # Allocate 1 GPU
```


## Frequently Asked Questions

### How to determine the embedding dimension of a model?

Different models have different embedding dimensions. Here are the dimensions of some commonly used models:
- BAAI/bge-large-en-v1.5: 1024
- BAAI/bge-base-en-v1.5: 768
- nomic-ai/nomic-embed-text-v1: 768
- sentence-transformers/all-mpnet-base-v2: 768

You can find this information in the model's documentation or get it through the TEI service's API.

### How to test if the TEI service is working properly?

After deploying the TEI service, you can use the following commands to test if the service is working properly:

```bash
# Get the TEI service endpoint
export TEI_SERVICE=$(kubectl get svc -l component=text-embeddings-inference -o jsonpath='{.items[0].metadata.name}')

# Test the embedding functionality
kubectl run -it --rm curl --image=curlimages/curl -- curl -X POST "http://${TEI_SERVICE}:8080/embed" \
  -H "Content-Type: application/json" \
  -d '{"inputs":"This is a test text"}'
```

### How to use TEI-generated embeddings in Milvus?

In Milvus, you can use TEI-generated embeddings for the following operations:

1. When creating a collection, specify the vector dimension to match the TEI model output dimension
2. Before inserting data, use the TEI service to convert text to vectors
3. When searching, similarly use the TEI service to convert query text to vectors

## Using Milvus Text Embedding Function

Milvus provides a text embedding function feature that allows you to generate vector embeddings directly within Milvus. You can configure Milvus to use TEI as the backend for this function.

### Using the Text Embedding Function in Milvus

1. Specify the embedding function when creating a collection:

```python
from pymilvus import MilvusClient, DataType, Function, FunctionType

# Connect to Milvus
client = MilvusClient(uri="http://localhost:19530")

# 1. Create schema
schema = client.create_schema()

# 2. Add fields
schema.add_field("id", DataType.INT64, is_primary=True, auto_id=False)  # Primary key
schema.add_field("text", DataType.VARCHAR, max_length=65535)             # Text field
schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=768)              # Vector field, dimension must match TEI model output

# 3. Define TEI embedding function
tei_embedding_function = Function(
    name="tei_func",                            # Unique identifier for this embedding function
    function_type=FunctionType.TEXTEMBEDDING,   # Indicates a text embedding function
    input_field_names=["text"],                # Scalar field(s) containing text data to embed
    output_field_names=["embedding"],             # Vector field(s) for storing embeddings
    params={                                    # TEI specific parameters
        "provider": "TEI",                   # Must be set to "TEI"
        "endpoint": "http://tei-service:8080", # TEI service address
        # Optional: "api_key": "your_secure_api_key",
        # Optional: "truncate": "true",
        # Optional: "truncation_direction": "right",
        # Optional: "max_client_batch_size": 64,
        # Optional: "ingestion_prompt": "passage: ",
        # Optional: "search_prompt": "query: "
    }
)
schema.add_function(tei_embedding_function)

# 4. Create collection with schema and index param
index_params = client.prepare_index_params()
index_params.add_index(
    field_name="embedding",
    index_name="embedding_index",
    index_type="HNSW",
    metric_type="COSINE",
)
client.create_collection(
    name="test_collection",
    schema=schema,
    index_params=index_params
)
client.load_collection(
    collection_name="test_collection"
)

```

2. Automatically generate embeddings when inserting data 

```python
# Insert data, Milvus will automatically call the TEI service to generate embedding vectors
client.insert(
    collection_name="test_collection",
    data=[
        {"id": 1, "text": "This is a sample document about artificial intelligence."},
        {"id": 2, "text": "Vector databases are designed to handle embeddings efficiently."}
    ]
)
```

3. Automatically generate query embeddings when searching:

```python
# Search directly using text, Milvus will automatically call the TEI service to generate query vectors
results = client.search(
    collection_name="test_collection",
    data=["Tell me about AI technology"],
    anns_field="embedding",
    search_params={
        "metric_type": "COSINE",
        "params": {}
    },
    limit=3
)
```
