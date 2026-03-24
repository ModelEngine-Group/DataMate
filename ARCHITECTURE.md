# DataMate Architecture

## Overview

DataMate is a microservices-based data management platform for model fine-tuning and RAG retrieval. It follows a polyglot architecture with Java backend, Python runtime, and React frontend.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                       │
│                      localhost:5173                          │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│                      (Spring Cloud)                           │
│                       localhost:8080                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Authentication (JWT)                                 │  │
│  │  Route Forwarding                                     │  │
│  │  Rate Limiting                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ├─────────────────┬─────────────────┐
                 ▼                 ▼                 ▼
┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
│  Main Application     │ │  Data Management      │ │  RAG Indexer         │
│  (Spring Boot)       │ │  Service              │ │  Service              │
│  - Data Cleaning      │ │  - Dataset Mgmt      │ │  - Knowledge Base     │
│  - Operator Market    │ │  - File Operations   │ │  - Vector Search      │
│  - Data Collection   │ │  - Tag Management    │ │  - Milvus Integration │
└─────────┬───────────┘ └─────────┬───────────┘ └─────────┬───────────┘
          │                       │                       │
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     PostgreSQL (Metadata)                              │
│                     Redis (Cache)                                    │
│                     Milvus (Vectors)                                  │
│                     MinIO (Files)                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Python Runtime (FastAPI)                     │
│                    localhost:18000                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Data Synthesis                                      │  │
│  │  Data Annotation (Label Studio)                        │  │
│  │  Data Evaluation                                      │  │
│  │  RAG Indexing                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              Ray Executor (Distributed)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Operator Execution                                   │  │
│  │  Task Scheduling                                      │  │
│  │  Distributed Computing                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### Frontend Layer
- **Framework**: React 18 + TypeScript + Vite
- **UI Library**: Ant Design
- **Styling**: TailwindCSS v4
- **State Management**: Redux Toolkit
- **Routing**: React Router v7

### Backend Layer (Java)
- **API Gateway**: Spring Cloud Gateway
  - Route forwarding
  - JWT authentication
  - Rate limiting

- **Main Application**: Spring Boot 3.5
  - Data cleaning pipeline
  - Operator marketplace
  - Data collection tasks

- **Data Management Service**: Spring Boot 3.5
  - Dataset CRUD
  - File operations
  - Tag management

- **RAG Indexer Service**: Spring Boot 3.5
  - Knowledge base management
  - Vector search
  - Milvus integration

### Runtime Layer (Python)
- **FastAPI Backend**: Port 18000
  - Data synthesis (QA generation)
  - Data annotation (Label Studio integration)
  - Model evaluation
  - RAG indexing

- **Ray Executor**: Distributed execution
  - Operator execution
  - Task scheduling
  - Multi-node parallelism

### Operator Ecosystem
- **filter**: Data filtering (duplicates, sensitive content, quality)
- **mapper**: Data transformation (cleaning, normalization)
- **slicer**: Data segmentation (text splitting, slide extraction)
- **formatter**: Format conversion (PDF → text, slide → JSON)
- **llms**: LLM-based operators (quality evaluation, condition checking)

## Data Flow

### 1. Data Ingestion
```
User Upload → Frontend → API Gateway → Data Management Service → PostgreSQL/MinIO
```

### 2. Data Processing
```
Dataset → Frontend → API Gateway → Main Application → Python Runtime
→ Ray Executor → Operators → Processed Data → PostgreSQL/MinIO
```

### 3. RAG Indexing
```
Processed Data → Python Runtime → RAG Indexer Service → Milvus (Vectors)
```

### 4. RAG Retrieval
```
Query → Frontend → API Gateway → RAG Indexer Service → Milvus → Results
```

## Technology Stack

| Layer | Technology |
|--------|-----------|
| **Frontend** | React 18, TypeScript, Vite, Ant Design, TailwindCSS |
| **Backend** | Spring Boot 3.5, Java 21, MyBatis-Plus, PostgreSQL |
| **Runtime** | FastAPI, Python 3.12, Ray, SQLAlchemy |
| **Vector DB** | Milvus |
| **Cache** | Redis |
| **Object Storage** | MinIO |
| **Deployment** | Docker Compose, Kubernetes/Helm |

## Communication Patterns

### Service-to-Service
- **REST API**: HTTP/JSON between frontend and backend
- **gRPC**: (if any) between backend services
- **Message Queue**: (if any) for async tasks

### Backend-to-Runtime
- **HTTP/REST**: Java backend calls Python runtime runtime APIs
- **Ray**: Python runtime submits tasks to Ray executor

## Security

### Authentication
- **JWT**: Token-based authentication via API Gateway
- **Session**: (if any) session management

### Authorization
- **Role-based**: (if any) RBAC
- **Resource-based**: (if any) resource-level access control

## Scalability

### Horizontal Scaling
- **Backend Services**: Kubernetes pod scaling via Helm
- **Ray Executor**: Multi-node Ray cluster
- **Frontend**: Static asset serving + CDN

### Vertical Scaling
- **Database**: PostgreSQL connection pooling
- **Cache**: Redis clustering
- **Vector DB**: Milvus cluster

## Deployment

### Docker Compose
```bash
make install INSTALLER=docker
```

### Kubernetes/Helm
```bash
make install INSTALLER=k8s
```

## Monitoring

### Metrics
- **Spring Boot Actuator**: `/actuator/metrics`
- **Prometheus**: (if configured) metrics collection
- **Ray**: Ray dashboard for executor monitoring

### Logging
- **Java**: Log4j2
- **Python**: Ray dashboard for executor monitoring

## Architecture Decisions

### Why Polyglot?
- **Java Backend**: Enterprise-grade, mature ecosystem, strong typing
- **Python Runtime**: Rich ML/AI ecosystem, flexible, fast prototyping
- **React Frontend**: Modern UI, component-based, large ecosystem

### Why Microservices?
- **Scalability**: Independent scaling of services
- **Maintainability**: Clear service boundaries
- **Technology Diversity**: Use best tool for each job

### Why Ray?
- **Distributed Computing**: Seamless multi-node execution
- **Fault Tolerance**: Automatic task retry and recovery
- **Resource Management**: Dynamic resource allocation

## Future Enhancements

- [ ] Service Mesh (Istio/Linkerd)
- [ ] Event Bus (Kafka/Pulsar)
- [ ] GraphQL API
- [ ] Real-time-Updates (WebSocket)
- [ ] Advanced Monitoring (Grafana, Loki)

## References

- [Backend Architecture](./backend/README.md)
- [Runtime Architecture](./runtime/README.md)
- [Frontend Architecture](./frontend/README.md)
- [AGENTS.md](./AGENTS.md)
