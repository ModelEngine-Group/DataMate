"use client";

import type React from "react";

import { useState } from "react";
import {
  Card,
  Button,
  Input,
  Select,
  Badge,
  Progress,
  Switch,
  Tabs,
  Checkbox,
} from "antd";
import { SearchControls } from "@/components/SearchControls";
import {
  BookOpen,
  Plus,
  Search,
  Eye,
  Upload,
  Database,
  Settings,
  Edit,
  ChevronRight,
  File,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Brain,
  Layers,
  Split,
  MoreHorizontal,
  Trash2,
  Folder,
  Download,
  Calendar,
  History,
  RefreshCw,
  Scissors,
  VideoIcon as Vector,
  Server,
  FileText,
  ArrowLeft,
  Save,
  Zap,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";

interface KnowledgeBase {
  id: number;
  name: string;
  description: string;
  type: "unstructured" | "structured";
  status: "processing" | "ready" | "error" | "importing" | "vectorizing";
  fileCount: number;
  chunkCount: number;
  vectorCount: number;
  size: string;
  progress: number;
  createdAt: string;
  lastUpdated: string;
  vectorDatabase: string;
  config: {
    embeddingModel: string;
    llmModel?: string;
    chunkSize: number;
    overlap: number;
    sliceMethod: "paragraph" | "length" | "delimiter" | "semantic";
    delimiter?: string;
    enableQA: boolean;
    vectorDimension: number;
    sliceOperators: string[];
  };
  files: KBFile[];
  vectorizationHistory: VectorizationRecord[];
}

interface KBFile {
  id: number;
  name: string;
  type: string;
  size: string;
  status: "processing" | "completed" | "error" | "disabled" | "vectorizing";
  chunkCount: number;
  progress: number;
  uploadedAt: string;
  source: "upload" | "dataset";
  datasetId?: string;
  chunks?: Chunk[];
  vectorizationStatus?: "pending" | "processing" | "completed" | "failed";
}

interface Chunk {
  id: number;
  content: string;
  position: number;
  tokens: number;
  embedding?: number[];
  similarity?: string;
  createdAt?: string;
  updatedAt?: string;
  vectorId?: string;
  sliceOperator?: string;
  parentChunkId?: number;
  metadata?: {
    source: string;
    page?: number;
    section?: string;
  };
}

interface VectorizationRecord {
  id: number;
  timestamp: string;
  operation: "create" | "update" | "delete" | "reprocess";
  fileId: number;
  fileName: string;
  chunksProcessed: number;
  vectorsGenerated: number;
  status: "success" | "failed" | "partial";
  duration: string;
  config: {
    embeddingModel: string;
    chunkSize: number;
    sliceMethod: string;
  };
  error?: string;
}

interface MockDataset {
  id: string;
  name: string;
  files: { id: string; name: string; size: string; type: string }[];
}

interface SliceOperator {
  id: string;
  name: string;
  description: string;
  type: "text" | "semantic" | "structure" | "custom";
  icon: string;
  params: Record<string, any>;
}

const sliceOperators: SliceOperator[] = [
  {
    id: "paragraph-split",
    name: "段落分割",
    description: "按段落自然分割文档",
    type: "text",
    icon: "📄",
    params: { minLength: 50, maxLength: 1000 },
  },
  {
    id: "sentence-split",
    name: "句子分割",
    description: "按句子边界分割文档",
    type: "text",
    icon: "📝",
    params: { maxSentences: 5, overlap: 1 },
  },
  {
    id: "semantic-split",
    name: "语义分割",
    description: "基于语义相似度智能分割",
    type: "semantic",
    icon: "🧠",
    params: { threshold: 0.7, windowSize: 3 },
  },
  {
    id: "length-split",
    name: "长度分割",
    description: "按固定字符长度分割",
    type: "text",
    icon: "📏",
    params: { chunkSize: 512, overlap: 50 },
  },
  {
    id: "structure-split",
    name: "结构化分割",
    description: "按文档结构（标题、章节）分割",
    type: "structure",
    icon: "🏗️",
    params: { preserveHeaders: true, minSectionLength: 100 },
  },
  {
    id: "table-extract",
    name: "表格提取",
    description: "提取并单独处理表格内容",
    type: "structure",
    icon: "📊",
    params: { includeHeaders: true, mergeRows: false },
  },
  {
    id: "code-extract",
    name: "代码提取",
    description: "识别并提取代码块",
    type: "custom",
    icon: "💻",
    params: {
      languages: ["python", "javascript", "sql"],
      preserveIndentation: true,
    },
  },
  {
    id: "qa-extract",
    name: "问答提取",
    description: "自动识别问答格式内容",
    type: "semantic",
    icon: "❓",
    params: { confidenceThreshold: 0.8, generateAnswers: true },
  },
];

const vectorDatabases = [
  {
    id: "pinecone",
    name: "Pinecone",
    description: "云端向量数据库，高性能检索",
  },
  {
    id: "weaviate",
    name: "Weaviate",
    description: "开源向量数据库，支持多模态",
  },
  { id: "qdrant", name: "Qdrant", description: "高性能向量搜索引擎" },
  { id: "chroma", name: "ChromaDB", description: "轻量级向量数据库" },
  { id: "milvus", name: "Milvus", description: "分布式向量数据库" },
  { id: "faiss", name: "FAISS", description: "Facebook AI 相似性搜索库" },
];

const mockKnowledgeBases: KnowledgeBase[] = [
  {
    id: 1,
    name: "产品技术文档库",
    description:
      "包含所有产品相关的技术文档和API说明，支持多种格式文档的智能解析和向量化处理",
    type: "unstructured",
    status: "ready",
    fileCount: 45,
    chunkCount: 1250,
    vectorCount: 1250,
    size: "2.3 GB",
    progress: 100,
    createdAt: "2024-01-15",
    lastUpdated: "2024-01-22",
    vectorDatabase: "pinecone",
    config: {
      embeddingModel: "text-embedding-3-large",
      llmModel: "gpt-4o",
      chunkSize: 512,
      overlap: 50,
      sliceMethod: "semantic",
      enableQA: true,
      vectorDimension: 1536,
      sliceOperators: ["semantic-split", "paragraph-split", "table-extract"],
    },
    files: [
      {
        id: 1,
        name: "API文档.pdf",
        type: "pdf",
        size: "2.5 MB",
        status: "completed",
        chunkCount: 156,
        progress: 100,
        uploadedAt: "2024-01-15",
        source: "upload",
        vectorizationStatus: "completed",
      },
      {
        id: 2,
        name: "用户手册.docx",
        type: "docx",
        size: "1.8 MB",
        status: "disabled",
        chunkCount: 89,
        progress: 65,
        uploadedAt: "2024-01-22",
        source: "dataset",
        datasetId: "dataset-1",
        vectorizationStatus: "failed",
      },
    ],
    vectorizationHistory: [
      {
        id: 1,
        timestamp: "2024-01-22 14:30:00",
        operation: "create",
        fileId: 1,
        fileName: "API文档.pdf",
        chunksProcessed: 156,
        vectorsGenerated: 156,
        status: "success",
        duration: "2m 15s",
        config: {
          embeddingModel: "text-embedding-3-large",
          chunkSize: 512,
          sliceMethod: "semantic",
        },
      },
      {
        id: 2,
        timestamp: "2024-01-22 15:45:00",
        operation: "update",
        fileId: 2,
        fileName: "用户手册.docx",
        chunksProcessed: 89,
        vectorsGenerated: 0,
        status: "failed",
        duration: "0m 45s",
        config: {
          embeddingModel: "text-embedding-3-large",
          chunkSize: 512,
          sliceMethod: "semantic",
        },
        error: "向量化服务连接超时",
      },
    ],
  },
  {
    id: 2,
    name: "FAQ结构化知识库",
    description: "客服常见问题的结构化问答对，支持快速检索和智能匹配",
    type: "structured",
    status: "vectorizing",
    fileCount: 12,
    chunkCount: 890,
    vectorCount: 750,
    size: "156 MB",
    progress: 75,
    createdAt: "2024-01-20",
    lastUpdated: "2024-01-23",
    vectorDatabase: "weaviate",
    config: {
      embeddingModel: "text-embedding-ada-002",
      chunkSize: 256,
      overlap: 0,
      sliceMethod: "paragraph",
      enableQA: false,
      vectorDimension: 1536,
      sliceOperators: ["qa-extract", "paragraph-split"],
    },
    files: [
      {
        id: 3,
        name: "FAQ模板.xlsx",
        type: "xlsx",
        size: "450 KB",
        status: "vectorizing",
        chunkCount: 234,
        progress: 75,
        uploadedAt: "2024-01-20",
        source: "upload",
        vectorizationStatus: "processing",
      },
    ],
    vectorizationHistory: [],
  },
];

const mockDatasets: MockDataset[] = [
  {
    id: "dataset-1",
    name: "客户反馈数据集",
    files: [
      {
        id: "file-a",
        name: "2023年Q4客户反馈.txt",
        size: "1.2 MB",
        type: "txt",
      },
      { id: "file-b", name: "产品评论汇总.csv", size: "800 KB", type: "csv" },
      { id: "file-c", name: "用户满意度调查.pdf", size: "3.5 MB", type: "pdf" },
    ],
  },
  {
    id: "dataset-2",
    name: "市场研究报告",
    files: [
      {
        id: "file-d",
        name: "行业分析报告2024.pdf",
        size: "5.1 MB",
        type: "pdf",
      },
      { id: "file-e", name: "竞品分析.docx", size: "2.1 MB", type: "docx" },
    ],
  },
  {
    id: "dataset-3",
    name: "内部知识库文档",
    files: [
      { id: "file-f", name: "公司规章制度.pdf", size: "1.5 MB", type: "pdf" },
      {
        id: "file-g",
        name: "新员工入职指南.docx",
        size: "0.9 MB",
        type: "docx",
      },
      { id: "file-h", name: "技术规范V1.0.txt", size: "0.7 MB", type: "txt" },
    ],
  },
];

export default function KnowledgeGenerationPage() {
  const [knowledgeBases, setKnowledgeBases] =
    useState<KnowledgeBase[]>(mockKnowledgeBases);
  const [selectedKB, setSelectedKB] = useState<KnowledgeBase | null>(null);
  const [selectedFile, setSelectedFile] = useState<KBFile | null>(null);
  const [currentView, setCurrentView] = useState<
    "list" | "detail" | "file" | "create" | "edit" | "config"
  >("list");
  const [searchQuery, setSearchQuery] = useState("");

  const [typeFilter, setTypeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState<
    "name" | "size" | "fileCount" | "createdAt"
  >("createdAt");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [viewMode, setViewMode] = useState<"card" | "table">("card");
  const [searchTerm, setSearchTerm] = useState("");

  // New state for configuration
  const [configStep, setConfigStep] = useState<1 | 2 | 3>(1);
  const [slicingMode, setSlicingMode] = useState<"qa" | "chunk">("chunk");
  const [processingMethod, setProcessingMethod] = useState<
    "default" | "custom"
  >("default");
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [editingChunkMode, setEditingChunkMode] = useState<"chunk" | "qa">(
    "chunk"
  );
  const [showChunkEditDialog, setShowChunkEditDialog] = useState<Chunk | null>(
    null
  );
  const [chunkEditContent, setChunkEditContent] = useState("");
  const [qaQuestion, setQaQuestion] = useState("");
  const [qaAnswer, setQaAnswer] = useState("");

  const filterOptions = [
    {
      key: "type",
      label: "类型",
      options: [
        { label: "非结构化", value: "unstructured" },
        { label: "结构化", value: "structured" },
      ],
    },
    {
      key: "status",
      label: "状态",
      options: [
        { label: "就绪", value: "ready" },
        { label: "处理中", value: "processing" },
        { label: "向量化中", value: "vectorizing" },
        { label: "导入中", value: "importing" },
        { label: "错误", value: "error" },
      ],
    },
  ];

  const sortOptions = [
    { label: "名称", value: "name" },
    { label: "大小", value: "size" },
    { label: "文件数量", value: "fileCount" },
    { label: "创建时间", value: "createdAt" },
    { label: "修改时间", value: "lastModified" },
  ];

  // Filter and sort logic
  const filteredData = knowledgeBases.filter((item) => {
    // Search filter
    if (
      searchTerm &&
      !item.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !item.description.toLowerCase().includes(searchTerm.toLowerCase())
    ) {
      return false;
    }

    // Type filter
    if (typeFilter !== "all" && item.type !== typeFilter) {
      return false;
    }

    // Status filter
    if (statusFilter !== "all" && item.status !== statusFilter) {
      return false;
    }

    return true;
  });

  // Sort data
  if (sortBy) {
    filteredData.sort((a, b) => {
      let aValue: any = a[sortBy as keyof KnowledgeBase];
      let bValue: any = b[sortBy as keyof KnowledgeBase];

      if (sortBy === "size") {
        aValue = Number.parseFloat(aValue.replace(/[^\d.]/g, ""));
        bValue = Number.parseFloat(bValue.replace(/[^\d.]/g, ""));
      }

      if (typeof aValue === "string") {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (sortOrder === "asc") {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
  }

  const [createForm, setCreateForm] = useState({
    name: "",
    description: "",
    type: "unstructured" as "unstructured" | "structured",
    embeddingModel: "text-embedding-3-large",
    llmModel: "gpt-4o",
    chunkSize: 512,
    overlap: 50,
    sliceMethod: "semantic" as
      | "paragraph"
      | "length"
      | "delimiter"
      | "semantic",
    delimiter: "",
    enableQA: true,
    vectorDatabase: "pinecone",
    selectedSliceOperators: ["semantic-split", "paragraph-split"] as string[],
    uploadedFiles: [] as File[],
    selectedDatasetFiles: [] as {
      datasetId: string;
      fileId: string;
      name: string;
      size: string;
      type: string;
    }[],
  });

  const [editForm, setEditForm] = useState<KnowledgeBase | null>(null);
  const [datasetSearchQuery, setDatasetSearchQuery] = useState("");
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(
    null
  );
  const [detailTab, setDetailTab] = useState<
    "files" | "test" | "history" | "vectors"
  >("files");
  const [showSliceTraceDialog, setShowSliceTraceDialog] = useState<
    number | null
  >(null);
  const [showVectorizationDialog, setShowVectorizationDialog] = useState(false);
  const [showEditFileDialog, setShowEditFileDialog] = useState<KBFile | null>(
    null
  );

  const handleCreateKB = () => {
    const newKB: KnowledgeBase = {
      id: Date.now(),
      name: createForm.name,
      description: createForm.description,
      type: createForm.type,
      status: "importing",
      fileCount:
        createForm.uploadedFiles.length +
        createForm.selectedDatasetFiles.length,
      chunkCount: 0,
      vectorCount: 0,
      size: "0 MB",
      progress: 0,
      createdAt: new Date().toISOString().split("T")[0],
      lastUpdated: new Date().toISOString().split("T")[0],
      vectorDatabase: createForm.vectorDatabase,
      config: {
        embeddingModel: createForm.embeddingModel,
        llmModel: createForm.llmModel,
        chunkSize: createForm.chunkSize,
        overlap: createForm.overlap,
        sliceMethod: createForm.sliceMethod,
        delimiter: createForm.delimiter,
        enableQA: createForm.enableQA,
        vectorDimension: createForm.embeddingModel.includes("3-large")
          ? 3072
          : 1536,
        sliceOperators: createForm.selectedSliceOperators,
      },
      files: [
        ...createForm.uploadedFiles.map((file) => ({
          id: Date.now() + Math.random(),
          name: file.name,
          type: file.type.split("/")[1] || "unknown",
          size: `${(file.size / (1024 * 1024)).toFixed(2)} MB`,
          status: "processing" as const,
          chunkCount: 0,
          progress: 0,
          uploadedAt: new Date().toISOString().split("T")[0],
          source: "upload" as const,
          vectorizationStatus: "pending" as const,
        })),
        ...createForm.selectedDatasetFiles.map((file) => ({
          id: Date.now() + Math.random(),
          name: file.name,
          type: file.type,
          size: file.size,
          status: "processing" as const,
          chunkCount: 0,
          progress: 0,
          uploadedAt: new Date().toISOString().split("T")[0],
          source: "dataset" as const,
          datasetId: file.datasetId,
          vectorizationStatus: "pending" as const,
        })),
      ],
      vectorizationHistory: [],
    };

    setKnowledgeBases([newKB, ...knowledgeBases]);
    setCurrentView("list");
    resetCreateForm();

    // Simulate processing stages
    setTimeout(() => {
      setKnowledgeBases((prev) =>
        prev.map((kb) =>
          kb.id === newKB.id
            ? {
                ...kb,
                status: "processing",
                progress: 25,
                chunkCount: Math.floor(Math.random() * 500 + 100),
              }
            : kb
        )
      );
    }, 1000);

    setTimeout(() => {
      setKnowledgeBases((prev) =>
        prev.map((kb) =>
          kb.id === newKB.id
            ? {
                ...kb,
                status: "vectorizing",
                progress: 60,
              }
            : kb
        )
      );
    }, 3000);

    setTimeout(() => {
      setKnowledgeBases((prev) =>
        prev.map((kb) =>
          kb.id === newKB.id
            ? {
                ...kb,
                status: "ready",
                progress: 100,
                vectorCount: kb.chunkCount,
                size: `${(Math.random() * 2 + 0.5).toFixed(1)} GB`,
                files: kb.files.map((file) => ({
                  ...file,
                  status: "completed" as const,
                  progress: 100,
                  vectorizationStatus: "completed" as const,
                })),
                vectorizationHistory: [
                  {
                    id: 1,
                    timestamp: new Date()
                      .toISOString()
                      .replace("T", " ")
                      .split(".")[0],
                    operation: "create" as const,
                    fileId: kb.files[0]?.id || 0,
                    fileName: kb.files[0]?.name || "",
                    chunksProcessed: kb.chunkCount,
                    vectorsGenerated: kb.chunkCount,
                    status: "success" as const,
                    duration: "3m 45s",
                    config: {
                      embeddingModel: createForm.embeddingModel,
                      chunkSize: createForm.chunkSize,
                      sliceMethod: createForm.sliceMethod,
                    },
                  },
                ],
              }
            : kb
        )
      );
    }, 6000);
  };

  const resetCreateForm = () => {
    setCreateForm({
      name: "",
      description: "",
      type: "unstructured",
      embeddingModel: "text-embedding-3-large",
      llmModel: "gpt-4o",
      chunkSize: 512,
      overlap: 50,
      sliceMethod: "semantic",
      delimiter: "",
      enableQA: true,
      vectorDatabase: "pinecone",
      selectedSliceOperators: ["semantic-split", "paragraph-split"],
      uploadedFiles: [],
      selectedDatasetFiles: [],
    });
    setSelectedDatasetId(null);
  };

  const handleEditKB = () => {
    if (!editForm) return;

    setKnowledgeBases((prev) =>
      prev.map((kb) =>
        kb.id === editForm.id
          ? { ...editForm, lastUpdated: new Date().toISOString().split("T")[0] }
          : kb
      )
    );
    setSelectedKB(editForm);
    setCurrentView("detail");
    setEditForm(null);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "ready":
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "processing":
        return <Clock className="w-4 h-4 text-blue-500" />;
      case "vectorizing":
        return <Vector className="w-4 h-4 text-purple-500" />;
      case "importing":
        return <Upload className="w-4 h-4 text-orange-500" />;
      case "error":
        return <XCircle className="w-4 h-4 text-red-500" />;
      case "disabled":
        return <AlertCircle className="w-4 h-4 text-gray-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusLabel = (status: string) => {
    const labels = {
      ready: "就绪",
      processing: "处理中",
      vectorizing: "向量化中",
      importing: "导入中",
      error: "错误",
      disabled: "已禁用",
      completed: "已完成",
    };
    return labels[status as keyof typeof labels] || status;
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case "ready":
      case "completed":
        return "default";
      case "processing":
      case "vectorizing":
        return "secondary";
      case "importing":
        return "outline";
      case "error":
        return "destructive";
      default:
        return "outline";
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setCreateForm((prev) => ({
        ...prev,
        uploadedFiles: Array.from(event.target.files),
      }));
    }
  };

  const handleDatasetFileToggle = (
    datasetId: string,
    file: MockDataset["files"][0]
  ) => {
    setCreateForm((prev) => {
      const isSelected = prev.selectedDatasetFiles.some(
        (f) => f.datasetId === datasetId && f.fileId === file.id
      );
      if (isSelected) {
        return {
          ...prev,
          selectedDatasetFiles: prev.selectedDatasetFiles.filter(
            (f) => !(f.datasetId === datasetId && f.fileId === file.id)
          ),
        };
      } else {
        return {
          ...prev,
          selectedDatasetFiles: [
            ...prev.selectedDatasetFiles,
            { datasetId, ...file },
          ],
        };
      }
    });
  };

  const handleSelectAllDatasetFiles = (
    dataset: MockDataset,
    checked: boolean
  ) => {
    setCreateForm((prev) => {
      let newSelectedFiles = [...prev.selectedDatasetFiles];
      if (checked) {
        dataset.files.forEach((file) => {
          if (
            !newSelectedFiles.some(
              (f) => f.datasetId === dataset.id && f.fileId === file.id
            )
          ) {
            newSelectedFiles.push({ datasetId: dataset.id, ...file });
          }
        });
      } else {
        newSelectedFiles = newSelectedFiles.filter(
          (f) => f.datasetId !== dataset.id
        );
      }
      return { ...prev, selectedDatasetFiles: newSelectedFiles };
    });
  };

  const isDatasetFileSelected = (datasetId: string, fileId: string) => {
    return createForm.selectedDatasetFiles.some(
      (f) => f.datasetId === datasetId && f.fileId === fileId
    );
  };

  const isAllDatasetFilesSelected = (dataset: MockDataset) => {
    return dataset.files.every((file) =>
      isDatasetFileSelected(dataset.id, file.id)
    );
  };

  const filteredDatasets = mockDatasets.filter((dataset) =>
    dataset.name.toLowerCase().includes(datasetSearchQuery.toLowerCase())
  );

  const handleKBSelect = (kb: KnowledgeBase) => {
    setSelectedKB(kb);
    setCurrentView("detail");
  };

  const handleFileSelect = (file: KBFile) => {
    setSelectedFile(file);
    setCurrentView("file");
  };

  const handleDeleteKB = (kb: KnowledgeBase) => {
    if (confirm(`确定要删除知识库 "${kb.name}" 吗？此操作不可撤销。`)) {
      setKnowledgeBases((prev) => prev.filter((k) => k.id !== kb.id));
    }
  };

  const handleDeleteFile = (file: KBFile) => {
    if (confirm(`确定要删除文件 "${file.name}" 吗？`)) {
      setKnowledgeBases((prev) =>
        prev.map((kb) =>
          kb.id === selectedKB?.id
            ? {
                ...kb,
                files: kb.files.filter((f) => f.id !== file.id),
                fileCount: kb.fileCount - 1,
              }
            : kb
        )
      );
      if (selectedKB) {
        setSelectedKB((prev) =>
          prev
            ? {
                ...prev,
                files: prev.files.filter((f) => f.id !== file.id),
                fileCount: prev.fileCount - 1,
              }
            : null
        );
      }
    }
  };

  const handleStartVectorization = (fileId?: number) => {
    if (!selectedKB) return;

    const targetFiles = fileId ? [fileId] : selectedKB.files.map((f) => f.id);

    setKnowledgeBases((prev) =>
      prev.map((kb) =>
        kb.id === selectedKB.id
          ? {
              ...kb,
              status: "vectorizing",
              files: kb.files.map((file) =>
                targetFiles.includes(file.id)
                  ? { ...file, vectorizationStatus: "processing", progress: 0 }
                  : file
              ),
            }
          : kb
      )
    );

    // Simulate vectorization progress
    setTimeout(() => {
      setKnowledgeBases((prev) =>
        prev.map((kb) =>
          kb.id === selectedKB.id
            ? {
                ...kb,
                files: kb.files.map((file) =>
                  targetFiles.includes(file.id)
                    ? { ...file, progress: 50 }
                    : file
                ),
              }
            : kb
        )
      );
    }, 2000);

    setTimeout(() => {
      setKnowledgeBases((prev) =>
        prev.map((kb) =>
          kb.id === selectedKB.id
            ? {
                ...kb,
                status: "ready",
                files: kb.files.map((file) =>
                  targetFiles.includes(file.id)
                    ? {
                        ...file,
                        vectorizationStatus: "completed",
                        progress: 100,
                      }
                    : file
                ),
                vectorizationHistory: [
                  ...kb.vectorizationHistory,
                  {
                    id: Date.now(),
                    timestamp: new Date()
                      .toISOString()
                      .replace("T", " ")
                      .split(".")[0],
                    operation: "update" as const,
                    fileId: targetFiles[0],
                    fileName:
                      kb.files.find((f) => f.id === targetFiles[0])?.name || "",
                    chunksProcessed: Math.floor(Math.random() * 200 + 50),
                    vectorsGenerated: Math.floor(Math.random() * 200 + 50),
                    status: "success" as const,
                    duration: "1m 30s",
                    config: {
                      embeddingModel: kb.config.embeddingModel,
                      chunkSize: kb.config.chunkSize,
                      sliceMethod: kb.config.sliceMethod,
                    },
                  },
                ],
              }
            : kb
        )
      );
    }, 4000);
  };

  const handleSliceOperatorToggle = (operatorId: string) => {
    setCreateForm((prev) => ({
      ...prev,
      selectedSliceOperators: prev.selectedSliceOperators.includes(operatorId)
        ? prev.selectedSliceOperators.filter((id) => id !== operatorId)
        : [...prev.selectedSliceOperators, operatorId],
    }));
  };

  const [fileSearchQuery, setFileSearchQuery] = useState("");
  const [fileStatusFilter, setFileStatusFilter] = useState("all");

  const filteredFiles =
    selectedKB?.files.filter((file) => {
      const matchesSearch = file.name
        .toLowerCase()
        .includes(fileSearchQuery.toLowerCase());
      const matchesStatus =
        fileStatusFilter === "all" || file.status === fileStatusFilter;
      return matchesSearch && matchesStatus;
    }) || [];

  const [currentChunkPage, setCurrentChunkPage] = useState(1);
  const [editingChunk, setEditingChunk] = useState<number | null>(null);
  const [editChunkContent, setEditChunkContent] = useState("");
  const chunksPerPage = 5;

  const [chunkDetailModal, setChunkDetailModal] = useState<number | null>(null);

  const mockQAPairs = [
    {
      id: 1,
      question: "什么是API文档的主要用途？",
      answer:
        "API文档的主要用途是为开发者提供详细的接口说明，包括请求参数、响应格式和使用示例.",
    },
    {
      id: 2,
      question: "如何正确使用这个API？",
      answer:
        "使用API时需要先获取访问令牌，然后按照文档中的格式发送请求，注意处理错误响应.",
    },
  ];

  const handleViewChunkDetail = (chunkId: number) => {
    setChunkDetailModal(chunkId);
  };

  const mockChunks = Array.from({ length: 23 }, (_, i) => ({
    id: i + 1,
    content: `这是第 ${
      i + 1
    } 个文档分块的内容示例。在实际应用中，这里会显示从原始文档中提取和分割的具体文本内容。用户可以在这里查看和编辑分块的内容，确保知识库的质量和准确性。这个分块包含了重要的业务信息和技术细节，需要仔细维护以确保检索的准确性。`,
    position: i + 1,
    tokens: Math.floor(Math.random() * 200) + 100,
    embedding: Array.from({ length: 1536 }, () => Math.random() - 0.5),
    similarity: (Math.random() * 0.3 + 0.7).toFixed(3),
    createdAt: "2024-01-22 10:35",
    updatedAt: "2024-01-22 10:35",
    vectorId: `vec_${i + 1}_${Math.random().toString(36).substr(2, 9)}`,
    sliceOperator: ["semantic-split", "paragraph-split", "table-extract"][
      Math.floor(Math.random() * 3)
    ],
    parentChunkId: i > 0 ? Math.floor(Math.random() * i) + 1 : undefined,
    metadata: {
      source: "API文档.pdf",
      page: Math.floor(i / 5) + 1,
      section: `第${Math.floor(i / 3) + 1}章`,
    },
  }));

  // Three-step configuration view
  if (currentView === "config" && editForm) {
    const handleNextStep = () => {
      if (configStep === 1) {
        // Generate preview data based on current configuration
        const mockPreview = Array.from({ length: 5 }, (_, i) => ({
          id: i + 1,
          fileName:
            editForm.files[i % editForm.files.length]?.name || `文件${i + 1}`,
          chunks: Array.from(
            { length: Math.floor(Math.random() * 5) + 2 },
            (_, j) => ({
              id: `${i + 1}-${j + 1}`,
              content: `这是基于${
                slicingMode === "qa" ? "问答" : "分块"
              }模式和${processingMethod}处理方法生成的预览内容片段 ${
                j + 1
              }。内容会根据当前配置的切片大小${
                editForm.config.chunkSize
              }和重叠长度${editForm.config.overlap}进行处理。`,
              tokens: Math.floor(Math.random() * 100) + 50,
              type: slicingMode,
            })
          ),
        }));
        setPreviewData(mockPreview);
      }
      setConfigStep(Math.min(3, configStep + 1) as 1 | 2 | 3);
    };

    const handlePrevStep = () => {
      setConfigStep(Math.max(1, configStep - 1) as 1 | 2 | 3);
    };

    const handleConfirmConfig = () => {
      handleEditKB();
      setCurrentView("detail");
      setConfigStep(1);
    };

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">修改参数配置</h1>
            <p className="text-gray-600 mt-1">
              按步骤修改知识库的处理参数和配置
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setCurrentView("detail");
                setConfigStep(1);
              }}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回
            </Button>
          </div>
        </div>

        {/* Progress Steps */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-4">
                <div
                  className={`flex items-center justify-center w-8 h-8 rounded-full ${
                    configStep >= 1
                      ? "bg-blue-600 text-white"
                      : "bg-gray-200 text-gray-600"
                  }`}
                >
                  {configStep > 1 ? (
                    <CheckCircle2 className="w-5 h-5" />
                  ) : (
                    <span>1</span>
                  )}
                </div>
                <div
                  className={`h-px w-20 ${
                    configStep > 1 ? "bg-blue-600" : "bg-gray-300"
                  }`}
                />
                <div
                  className={`flex items-center justify-center w-8 h-8 rounded-full ${
                    configStep >= 2
                      ? "bg-blue-600 text-white"
                      : "bg-gray-200 text-gray-600"
                  }`}
                >
                  {configStep > 2 ? (
                    <CheckCircle2 className="w-5 h-5" />
                  ) : (
                    <span>2</span>
                  )}
                </div>
                <div
                  className={`h-px w-20 ${
                    configStep > 2 ? "bg-blue-600" : "bg-gray-300"
                  }`}
                />
                <div
                  className={`flex items-center justify-center w-8 h-8 rounded-full ${
                    configStep >= 3
                      ? "bg-blue-600 text-white"
                      : "bg-gray-200 text-gray-600"
                  }`}
                >
                  <span>3</span>
                </div>
              </div>
              <div className="text-sm text-gray-600">步骤 {configStep} / 3</div>
            </div>

            <div className="space-y-2 mb-6">
              <div className="flex justify-between text-sm text-gray-600">
                <span>修改参数</span>
                <span>预览数据</span>
                <span>确认上传</span>
              </div>
            </div>

            {/* Step 1: Modify Parameters */}
            {configStep === 1 && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold">第一步：修改参数配置</h3>

                <div className="grid grid-cols-2 gap-6">
                  <Card className="p-4">
                    <h4 className="font-medium mb-4">切片模式选择</h4>
                    <div className="space-y-3">
                      <div className="flex items-center space-x-3">
                        <input
                          type="radio"
                          id="chunk-mode"
                          name="slicing-mode"
                          checked={slicingMode === "chunk"}
                          onChange={() => setSlicingMode("chunk")}
                          className="w-4 h-4 text-blue-600"
                        />
                        <div>
                          <Label htmlFor="chunk-mode" className="font-medium">
                            Chunk 分块模式
                          </Label>
                          <p className="text-sm text-gray-600">
                            按固定大小将文档分割为文本块
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <input
                          type="radio"
                          id="qa-mode"
                          name="slicing-mode"
                          checked={slicingMode === "qa"}
                          onChange={() => setSlicingMode("qa")}
                          className="w-4 h-4 text-blue-600"
                        />
                        <div>
                          <Label htmlFor="qa-mode" className="font-medium">
                            QA 问答模式
                          </Label>
                          <p className="text-sm text-gray-600">
                            将文档内容转换为问答对格式
                          </p>
                        </div>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-4">
                    <h4 className="font-medium mb-4">切片大小限制</h4>
                    <div className="space-y-3">
                      <div>
                        <Label>分块大小 (tokens)</Label>
                        <Input
                          type="number"
                          value={editForm.config.chunkSize}
                          onChange={(e) =>
                            setEditForm({
                              ...editForm,
                              config: {
                                ...editForm.config,
                                chunkSize: Number(e.target.value),
                              },
                            })
                          }
                          min="100"
                          max="2000"
                        />
                      </div>
                      <div>
                        <Label>重叠长度 (tokens)</Label>
                        <Input
                          type="number"
                          value={editForm.config.overlap}
                          onChange={(e) =>
                            setEditForm({
                              ...editForm,
                              config: {
                                ...editForm.config,
                                overlap: Number(e.target.value),
                              },
                            })
                          }
                          min="0"
                          max="500"
                        />
                      </div>
                    </div>
                  </Card>
                </div>

                <Card className="p-4">
                  <h4 className="font-medium mb-4">切片处理方法</h4>
                  <div className="space-y-4">
                    <div className="flex items-center space-x-3">
                      <input
                        type="radio"
                        id="default-processing"
                        name="processing-method"
                        checked={processingMethod === "default"}
                        onChange={() => setProcessingMethod("default")}
                        className="w-4 h-4 text-blue-600"
                      />
                      <div>
                        <Label
                          htmlFor="default-processing"
                          className="font-medium"
                        >
                          默认处理方法
                        </Label>
                        <p className="text-sm text-gray-600">
                          使用系统预设的切片算子和参数
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <input
                        type="radio"
                        id="custom-processing"
                        name="processing-method"
                        checked={processingMethod === "custom"}
                        onChange={() => setProcessingMethod("custom")}
                        className="w-4 h-4 text-blue-600"
                      />
                      <div>
                        <Label
                          htmlFor="custom-processing"
                          className="font-medium"
                        >
                          自定义处理方法
                        </Label>
                        <p className="text-sm text-gray-600">
                          自定义选择切片算子和调整参数
                        </p>
                      </div>
                    </div>

                    {processingMethod === "custom" && (
                      <div className="ml-6 p-4 bg-gray-50 rounded-lg">
                        <h5 className="font-medium mb-3">选择切片算子</h5>
                        <div className="grid grid-cols-2 gap-3">
                          {sliceOperators.map((operator) => (
                            <div
                              key={operator.id}
                              className="flex items-center space-x-2"
                            >
                              <Checkbox
                                id={operator.id}
                                checked={editForm.config.sliceOperators.includes(
                                  operator.id
                                )}
                                onCheckedChange={(checked) => {
                                  if (checked) {
                                    setEditForm({
                                      ...editForm,
                                      config: {
                                        ...editForm.config,
                                        sliceOperators: [
                                          ...editForm.config.sliceOperators,
                                          operator.id,
                                        ],
                                      },
                                    });
                                  } else {
                                    setEditForm({
                                      ...editForm,
                                      config: {
                                        ...editForm.config,
                                        sliceOperators:
                                          editForm.config.sliceOperators.filter(
                                            (id) => id !== operator.id
                                          ),
                                      },
                                    });
                                  }
                                }}
                              />
                              <Label htmlFor={operator.id} className="text-sm">
                                {operator.name}
                              </Label>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </Card>
              </div>
            )}

            {/* Step 2: Preview Data */}
            {configStep === 2 && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold">第二步：预览数据</h3>
                <p className="text-gray-600">根据当前配置预览文件切片效果</p>

                <div className="space-y-4">
                  {previewData.map((filePreview) => (
                    <Card key={filePreview.id} className="p-4">
                      <h4 className="font-medium mb-3 flex items-center gap-2">
                        <File className="w-4 h-4" />
                        {filePreview.fileName}
                      </h4>
                      <div className="space-y-2">
                        {filePreview.chunks.map((chunk: any) => (
                          <div
                            key={chunk.id}
                            className="p-3 bg-gray-50 rounded-lg"
                          >
                            <div className="flex items-center gap-2 mb-2">
                              <Badge variant="outline" className="text-xs">
                                {chunk.type === "qa" ? "问答" : "分块"}{" "}
                                {chunk.id}
                              </Badge>
                              <Badge variant="secondary" className="text-xs">
                                {chunk.tokens} tokens
                              </Badge>
                            </div>
                            <p className="text-sm text-gray-700">
                              {chunk.content}
                            </p>
                          </div>
                        ))}
                      </div>
                    </Card>
                  ))}
                </div>

                <Card className="p-4 bg-blue-50">
                  <h4 className="font-medium mb-2">配置预览</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">切片模式:</span>
                      <span className="ml-2 font-medium">
                        {slicingMode === "qa" ? "问答模式" : "分块模式"}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">处理方法:</span>
                      <span className="ml-2 font-medium">
                        {processingMethod === "default" ? "默认" : "自定义"}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">分块大小:</span>
                      <span className="ml-2 font-medium">
                        {editForm.config.chunkSize} tokens
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">重叠长度:</span>
                      <span className="ml-2 font-medium">
                        {editForm.config.overlap} tokens
                      </span>
                    </div>
                  </div>
                </Card>
              </div>
            )}

            {/* Step 3: Confirm Upload */}
            {configStep === 3 && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold">第三步：确认上传</h3>
                <p className="text-gray-600">确认要上传的文件列表和相关信息</p>

                <div className="space-y-4">
                  <h4 className="font-medium">待上传文件列表</h4>
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="text-left p-4 font-medium">文件名</th>
                          <th className="text-left p-4 font-medium">类型</th>
                          <th className="text-left p-4 font-medium">大小</th>
                          <th className="text-left p-4 font-medium">
                            预计分块数
                          </th>
                          <th className="text-left p-4 font-medium">状态</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {editForm.files.map((file) => (
                          <tr key={file.id}>
                            <td className="p-4 font-medium">{file.name}</td>
                            <td className="p-4">{file.type.toUpperCase()}</td>
                            <td className="p-4">{file.size}</td>
                            <td className="p-4">
                              {Math.ceil(
                                file.chunkCount *
                                  (editForm.config.chunkSize / 512)
                              )}
                            </td>
                            <td className="p-4">
                              <Badge
                                variant="outline"
                                className="text-green-600"
                              >
                                <CheckCircle className="w-3 h-3 mr-1" />
                                准备就绪
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="grid grid-cols-2 gap-6">
                    <Card className="p-4">
                      <h4 className="font-medium mb-3">处理概要</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">总文件数:</span>
                          <span className="font-medium">
                            {editForm.files.length}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">预计分块数:</span>
                          <span className="font-medium">
                            {editForm.files.reduce(
                              (sum, f) =>
                                sum +
                                Math.ceil(
                                  f.chunkCount *
                                    (editForm.config.chunkSize / 512)
                                ),
                              0
                            )}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">预计向量数:</span>
                          <span className="font-medium">
                            {editForm.files.reduce(
                              (sum, f) =>
                                sum +
                                Math.ceil(
                                  f.chunkCount *
                                    (editForm.config.chunkSize / 512)
                                ),
                              0
                            )}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">预计处理时间:</span>
                          <span className="font-medium">
                            约 {Math.ceil(editForm.files.length * 0.5)} 分钟
                          </span>
                        </div>
                      </div>
                    </Card>

                    <Card className="p-4">
                      <h4 className="font-medium mb-3">配置详情</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">切片模式:</span>
                          <span className="font-medium">
                            {slicingMode === "qa" ? "问答模式" : "分块模式"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">处理方法:</span>
                          <span className="font-medium">
                            {processingMethod === "default" ? "默认" : "自定义"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">嵌入模型:</span>
                          <span className="font-medium">
                            {editForm.config.embeddingModel}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">向量数据库:</span>
                          <span className="font-medium">
                            {
                              vectorDatabases.find(
                                (db) => db.id === editForm.vectorDatabase
                              )?.name
                            }
                          </span>
                        </div>
                      </div>
                    </Card>
                  </div>
                </div>
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex justify-between pt-6 border-t">
              <Button
                variant="outline"
                onClick={handlePrevStep}
                disabled={configStep === 1}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                上一步
              </Button>

              <div className="flex gap-2">
                {configStep < 3 ? (
                  <Button onClick={handleNextStep}>
                    下一步
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                ) : (
                  <Button
                    onClick={handleConfirmConfig}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    确认配置
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Create view
  if (currentView === "create") {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">创建知识库</h1>
            <p className="text-gray-600 mt-1">
              配置知识库参数，支持结构化和非结构化数据处理
            </p>
          </div>
          <Button variant="outline" onClick={() => setCurrentView("list")}>
            取消
          </Button>
        </div>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-6">
              <div className="space-y-4">
                <h4 className="font-medium">基本信息</h4>
                <div className="space-y-3">
                  <div>
                    <Label htmlFor="kb-name">
                      知识库名称 <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id="kb-name"
                      value={createForm.name}
                      onChange={(e) =>
                        setCreateForm({ ...createForm, name: e.target.value })
                      }
                      placeholder="输入知识库名称"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="kb-description">描述</Label>
                    <Textarea
                      id="kb-description"
                      value={createForm.description}
                      onChange={(e) =>
                        setCreateForm({
                          ...createForm,
                          description: e.target.value,
                        })
                      }
                      placeholder="描述知识库的用途和内容"
                      rows={3}
                    />
                  </div>
                  <div>
                    <Label>知识库类型</Label>
                    <div className="grid grid-cols-2 gap-4">
                      <Button
                        variant="outline"
                        onClick={() =>
                          setCreateForm({ ...createForm, type: "unstructured" })
                        }
                        className={`h-auto py-4 flex flex-col items-center gap-2 transition-all duration-200 ${
                          createForm.type === "unstructured"
                            ? "bg-blue-600 text-white border-blue-600 shadow-lg"
                            : "bg-white text-gray-800 border-gray-300 hover:bg-gray-50"
                        }`}
                      >
                        <BookOpen className="w-6 h-6" />
                        <p className="font-medium">非结构化知识库</p>
                        <p className="text-xs text-center opacity-80">
                          支持文档、PDF等文件
                        </p>
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() =>
                          setCreateForm({ ...createForm, type: "structured" })
                        }
                        className={`h-auto py-4 flex flex-col items-center gap-2 transition-all duration-200 ${
                          createForm.type === "structured"
                            ? "bg-blue-600 text-white border-blue-600 shadow-lg"
                            : "bg-white text-gray-800 border-gray-300 hover:bg-gray-50"
                        }`}
                      >
                        <Database className="w-6 h-6" />
                        <p className="font-medium">结构化知识库</p>
                        <p className="text-xs text-center opacity-80">
                          支持问答对、表格数据
                        </p>
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h4 className="font-medium flex items-center gap-2">
                  <Brain className="w-4 h-4" />
                  模型配置
                </h4>
                <div className="space-y-3">
                  <div>
                    <Label htmlFor="embedding-model">嵌入模型</Label>
                    <Select
                      value={createForm.embeddingModel}
                      onValueChange={(value) =>
                        setCreateForm({ ...createForm, embeddingModel: value })
                      }
                    >
                      <SelectTrigger id="embedding-model">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="text-embedding-3-large">
                          text-embedding-3-large (推荐)
                        </SelectItem>
                        <SelectItem value="text-embedding-3-small">
                          text-embedding-3-small
                        </SelectItem>
                        <SelectItem value="text-embedding-ada-002">
                          text-embedding-ada-002
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  {createForm.type === "unstructured" &&
                    createForm.enableQA && (
                      <div>
                        <Label htmlFor="llm-model">LLM模型 (用于Q&A生成)</Label>
                        <Select
                          value={createForm.llmModel}
                          onValueChange={(value) =>
                            setCreateForm({ ...createForm, llmModel: value })
                          }
                        >
                          <SelectTrigger id="llm-model">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="gpt-4o">
                              GPT-4o (推荐)
                            </SelectItem>
                            <SelectItem value="gpt-4o-mini">
                              GPT-4o Mini
                            </SelectItem>
                            <SelectItem value="gpt-3.5-turbo">
                              GPT-3.5 Turbo
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    )}
                </div>
              </div>

              <Separator />

              {createForm.type === "unstructured" && (
                <>
                  <div className="space-y-4">
                    <h4 className="font-medium flex items-center gap-2">
                      <Split className="w-4 h-4" />
                      文档分割配置
                    </h4>
                    <div className="space-y-3">
                      <div>
                        <Label htmlFor="slice-method">分割方式</Label>
                        <Select
                          value={createForm.sliceMethod}
                          onValueChange={(value: any) =>
                            setCreateForm({ ...createForm, sliceMethod: value })
                          }
                        >
                          <SelectTrigger id="slice-method">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="semantic">
                              语义分割 (推荐)
                            </SelectItem>
                            <SelectItem value="paragraph">段落分割</SelectItem>
                            <SelectItem value="length">长度分割</SelectItem>
                            <SelectItem value="delimiter">
                              分隔符分割
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      {createForm.sliceMethod === "delimiter" && (
                        <div>
                          <Label htmlFor="delimiter">分隔符</Label>
                          <Input
                            id="delimiter"
                            value={createForm.delimiter}
                            onChange={(e) =>
                              setCreateForm({
                                ...createForm,
                                delimiter: e.target.value,
                              })
                            }
                            placeholder="输入分隔符，如 \\n\\n"
                          />
                        </div>
                      )}

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label htmlFor="chunk-size">分块大小</Label>
                          <Input
                            id="chunk-size"
                            type="number"
                            value={createForm.chunkSize}
                            onChange={(e) =>
                              setCreateForm({
                                ...createForm,
                                chunkSize: Number(e.target.value),
                              })
                            }
                          />
                        </div>
                        <div>
                          <Label htmlFor="overlap-length">重叠长度</Label>
                          <Input
                            id="overlap-length"
                            type="number"
                            value={createForm.overlap}
                            onChange={(e) =>
                              setCreateForm({
                                ...createForm,
                                overlap: Number(e.target.value),
                              })
                            }
                          />
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <Label htmlFor="enable-qa">启用Q&A生成</Label>
                          <p className="text-xs text-gray-500">
                            将文档内容转换为问答对
                          </p>
                        </div>
                        <Switch
                          id="enable-qa"
                          checked={createForm.enableQA}
                          onCheckedChange={(checked) =>
                            setCreateForm({ ...createForm, enableQA: checked })
                          }
                        />
                      </div>
                    </div>
                  </div>

                  <Separator />
                </>
              )}

              <div className="space-y-4">
                <h4 className="font-medium flex items-center gap-2">
                  <Upload className="w-4 h-4" />
                  {createForm.type === "structured"
                    ? "导入模板文件"
                    : "选择数据源"}
                </h4>

                <Tabs defaultValue="upload">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="upload">上传文件</TabsTrigger>
                    <TabsTrigger value="dataset">从数据集选择</TabsTrigger>
                  </TabsList>

                  <TabsContent value="upload" className="space-y-3">
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center relative">
                      <Input
                        id="file-upload"
                        type="file"
                        multiple
                        className="absolute inset-0 opacity-0 cursor-pointer"
                        onChange={handleFileChange}
                      />
                      <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                      <p className="text-sm text-gray-600">
                        {createForm.type === "structured"
                          ? "拖拽或点击上传Excel/CSV模板文件"
                          : "拖拽或点击上传文档文件"}
                      </p>
                      <Button
                        variant="outline"
                        className="mt-2 bg-transparent pointer-events-none"
                      >
                        选择文件
                      </Button>
                    </div>
                    {createForm.uploadedFiles.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-sm font-medium">已选择文件:</p>
                        <ul className="list-disc pl-5 text-sm text-gray-700">
                          {createForm.uploadedFiles.map((file, index) => (
                            <li key={index}>{file.name}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value="dataset" className="space-y-3">
                    <div className="flex gap-2 mb-4">
                      <Input
                        placeholder="搜索数据集..."
                        value={datasetSearchQuery}
                        onChange={(e) => setDatasetSearchQuery(e.target.value)}
                        className="flex-1"
                      />
                      <Button
                        variant="outline"
                        onClick={() => setSelectedDatasetId(null)}
                      >
                        重置选择
                      </Button>
                    </div>

                    <div className="grid grid-cols-3 gap-4 h-80">
                      <div className="col-span-1 border rounded-lg overflow-y-auto p-2 space-y-2">
                        {filteredDatasets.length === 0 && (
                          <p className="text-center text-gray-500 py-4 text-sm">
                            无匹配数据集
                          </p>
                        )}
                        {filteredDatasets.map((dataset) => (
                          <div
                            key={dataset.id}
                            className={`flex items-center justify-between p-3 border rounded-lg cursor-pointer ${
                              selectedDatasetId === dataset.id
                                ? "bg-blue-50 border-blue-500"
                                : "hover:bg-gray-50"
                            }`}
                            onClick={() => setSelectedDatasetId(dataset.id)}
                          >
                            <div className="flex items-center gap-3">
                              <Folder className="w-5 h-5 text-blue-400" />
                              <div>
                                <p className="font-medium">{dataset.name}</p>
                                <p className="text-xs text-gray-500">
                                  {dataset.files.length} 个文件
                                </p>
                              </div>
                            </div>
                            {selectedDatasetId === dataset.id && (
                              <CheckCircle className="w-5 h-5 text-blue-600" />
                            )}
                          </div>
                        ))}
                      </div>

                      <div className="col-span-2 border rounded-lg overflow-y-auto p-2 space-y-2">
                        {!selectedDatasetId ? (
                          <div className="text-center py-8 text-gray-500">
                            <Folder className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                            <p className="text-sm">请选择一个数据集</p>
                          </div>
                        ) : (
                          <>
                            <div className="flex items-center gap-2 p-2 border-b pb-2">
                              <Checkbox
                                checked={isAllDatasetFilesSelected(
                                  mockDatasets.find(
                                    (d) => d.id === selectedDatasetId
                                  )!
                                )}
                                onCheckedChange={(checked) =>
                                  handleSelectAllDatasetFiles(
                                    mockDatasets.find(
                                      (d) => d.id === selectedDatasetId
                                    )!,
                                    checked as boolean
                                  )
                                }
                              />
                              <Label className="font-medium">
                                全选 (
                                {
                                  mockDatasets.find(
                                    (d) => d.id === selectedDatasetId
                                  )?.files.length
                                }{" "}
                                个文件)
                              </Label>
                            </div>
                            {mockDatasets
                              .find((d) => d.id === selectedDatasetId)
                              ?.files.map((file) => (
                                <div
                                  key={file.id}
                                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                                >
                                  <div className="flex items-center gap-3">
                                    <Checkbox
                                      checked={isDatasetFileSelected(
                                        selectedDatasetId,
                                        file.id
                                      )}
                                      onCheckedChange={(checked) =>
                                        handleDatasetFileToggle(
                                          selectedDatasetId,
                                          file
                                        )
                                      }
                                    />
                                    <File className="w-5 h-5 text-gray-400" />
                                    <div>
                                      <p className="font-medium">{file.name}</p>
                                      <p className="text-sm text-gray-500">
                                        {file.size} • {file.type}
                                      </p>
                                    </div>
                                  </div>
                                </div>
                              ))}
                          </>
                        )}
                      </div>
                    </div>
                    {createForm.selectedDatasetFiles.length > 0 && (
                      <div className="mt-4 text-sm font-medium text-gray-700">
                        已选择数据集文件总数:{" "}
                        {createForm.selectedDatasetFiles.length}
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </div>

              <div className="flex gap-3 pt-4">
                <Button
                  onClick={handleCreateKB}
                  disabled={!createForm.name || !createForm.description}
                  className="flex-1"
                >
                  创建知识库
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setCurrentView("list")}
                >
                  取消
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Edit view
  if (currentView === "edit" && editForm) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">编辑知识库</h1>
            <p className="text-gray-600 mt-1">修改知识库配置和文件</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setCurrentView("detail")}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回
            </Button>
          </div>
        </div>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-6">
              <div className="space-y-4">
                <h4 className="font-medium">基本信息</h4>
                <div className="space-y-3">
                  <div>
                    <Label htmlFor="edit-kb-name">知识库名称</Label>
                    <Input
                      id="edit-kb-name"
                      value={editForm.name}
                      onChange={(e) =>
                        setEditForm({ ...editForm, name: e.target.value })
                      }
                    />
                  </div>
                  <div>
                    <Label htmlFor="edit-kb-description">描述</Label>
                    <Textarea
                      id="edit-kb-description"
                      value={editForm.description}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          description: e.target.value,
                        })
                      }
                      rows={3}
                    />
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h4 className="font-medium flex items-center gap-2">
                  <Settings className="w-4 h-4" />
                  配置设置
                </h4>
                <div className="space-y-3">
                  <div>
                    <Label>嵌入模型</Label>
                    <Select
                      value={editForm.config.embeddingModel}
                      onValueChange={(value) =>
                        setEditForm({
                          ...editForm,
                          config: { ...editForm.config, embeddingModel: value },
                        })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="text-embedding-3-large">
                          text-embedding-3-large
                        </SelectItem>
                        <SelectItem value="text-embedding-3-small">
                          text-embedding-3-small
                        </SelectItem>
                        <SelectItem value="text-embedding-ada-002">
                          text-embedding-ada-002
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label>分块大小</Label>
                      <Input
                        type="number"
                        value={editForm.config.chunkSize}
                        onChange={(e) =>
                          setEditForm({
                            ...editForm,
                            config: {
                              ...editForm.config,
                              chunkSize: Number(e.target.value),
                            },
                          })
                        }
                      />
                    </div>
                    <div>
                      <Label>重叠长度</Label>
                      <Input
                        type="number"
                        value={editForm.config.overlap}
                        onChange={(e) =>
                          setEditForm({
                            ...editForm,
                            config: {
                              ...editForm.config,
                              overlap: Number(e.target.value),
                            },
                          })
                        }
                      />
                    </div>
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h4 className="font-medium flex items-center gap-2">
                  <File className="w-4 h-4" />
                  文件管理
                </h4>
                <div className="space-y-3">
                  {editForm.files.map((file) => (
                    <div
                      key={file.id}
                      className="flex items-center justify-between p-3 border rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <File className="w-5 h-5 text-gray-400" />
                        <div>
                          <p className="font-medium">{file.name}</p>
                          <div className="flex items-center gap-2 text-sm text-gray-500">
                            <span>{file.size}</span>
                            <Badge variant="outline" className="text-xs">
                              {file.source === "upload"
                                ? "上传文件"
                                : "数据集文件"}
                            </Badge>
                            {file.source === "dataset" && (
                              <Badge variant="outline" className="text-xs">
                                数据集: {file.datasetId}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setShowEditFileDialog(file)}
                        >
                          <Edit className="w-4 h-4 mr-1" />
                          编辑
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDeleteFile(file)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                  <Button variant="outline" className="w-full bg-transparent">
                    <Plus className="w-4 h-4 mr-2" />
                    添加文件
                  </Button>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <Button onClick={handleEditKB} className="flex-1">
                  <Save className="w-4 h-4 mr-2" />
                  保存更改
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setCurrentView("detail")}
                >
                  取消
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // File detail view
  if (currentView === "file" && selectedFile) {
    const totalPages = Math.ceil(mockChunks.length / chunksPerPage);
    const startIndex = (currentChunkPage - 1) * chunksPerPage;
    const currentChunks = mockChunks.slice(
      startIndex,
      startIndex + chunksPerPage
    );

    const handleEditChunk = (chunkId: number, content: string) => {
      setEditingChunk(chunkId);
      setEditChunkContent(content);
    };

    const handleSaveChunk = (chunkId: number) => {
      alert(`保存分块 ${chunkId} 的修改`);
      setEditingChunk(null);
      setEditChunkContent("");
    };

    const handleDeleteChunk = (chunkId: number) => {
      if (confirm(`确定要删除分块 ${chunkId} 吗？`)) {
        alert(`删除分块 ${chunkId}`);
      }
    };

    const handleSaveChunkEdit = () => {
      if (!showChunkEditDialog) return;

      if (showChunkEditDialog.id === 0) {
        // Adding new chunk
        alert("添加新的数据索引");
      } else {
        // Editing existing chunk
        alert(`更新分块 ${showChunkEditDialog.id}`);
      }

      setShowChunkEditDialog(null);
      setChunkEditContent("");
      setQaQuestion("");
      setQaAnswer("");
    };

    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <button
            onClick={() => setCurrentView("list")}
            className="hover:text-blue-600"
          >
            知识库
          </button>
          <ChevronRight className="w-4 h-4" />
          <button
            onClick={() => setCurrentView("detail")}
            className="hover:text-blue-600"
          >
            {selectedKB?.name}
          </button>
          <ChevronRight className="w-4 h-4" />
          <span>{selectedFile.name}</span>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <File className="w-5 h-5" />
                  {selectedFile.name}
                </CardTitle>
                {/* File metadata below filename */}
                <div className="mt-3 p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium mb-2">文件元数据</h4>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">文件类型:</span>
                      <span className="ml-2 font-medium">
                        {selectedFile.type}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">文件大小:</span>
                      <span className="ml-2 font-medium">
                        {selectedFile.size}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">上传时间:</span>
                      <span className="ml-2 font-medium">
                        {selectedFile.uploadedAt}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">分块数量:</span>
                      <span className="ml-2 font-medium">
                        {selectedFile.chunkCount}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">向量化状态:</span>
                      <Badge
                        variant={getStatusBadgeVariant(
                          selectedFile.vectorizationStatus || "pending"
                        )}
                        className="ml-2"
                      >
                        {getStatusLabel(
                          selectedFile.vectorizationStatus || "pending"
                        )}
                      </Badge>
                    </div>
                    <div>
                      <span className="text-gray-600">数据源:</span>
                      <span className="ml-2 font-medium">
                        {selectedFile.source === "upload"
                          ? "上传文件"
                          : "数据集文件"}
                      </span>
                    </div>
                  </div>
                </div>
                <CardDescription className="mt-2">
                  {selectedFile.size} • {selectedFile.chunkCount} 个分块 •{" "}
                  {getStatusLabel(selectedFile.status)}
                  {selectedFile.source === "dataset" && (
                    <Badge variant="outline" className="ml-2">
                      数据集: {selectedFile.datasetId}
                    </Badge>
                  )}
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSliceTraceDialog(selectedFile.id)}
                >
                  <History className="w-4 h-4 mr-1" />
                  切片回溯
                </Button>
                {selectedFile.vectorizationStatus !== "completed" && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleStartVectorization(selectedFile.id)}
                  >
                    <Vector className="w-4 h-4 mr-1" />
                    开始向量化
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="chunks">
              <TabsList>
                <TabsTrigger value="chunks">分块内容</TabsTrigger>
                <TabsTrigger value="vectors">向量信息</TabsTrigger>
                <TabsTrigger value="metadata">元数据</TabsTrigger>
                <TabsTrigger value="processing">处理日志</TabsTrigger>
              </TabsList>

              <TabsContent value="chunks" className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-600">
                    共 {mockChunks.length} 个分块，第 {startIndex + 1}-
                    {Math.min(startIndex + chunksPerPage, mockChunks.length)} 个
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setShowChunkEditDialog({
                          id: 0,
                          content: "",
                          position: mockChunks.length + 1,
                          tokens: 0,
                        })
                      }
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      添加新索引
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setCurrentChunkPage(Math.max(1, currentChunkPage - 1))
                      }
                      disabled={currentChunkPage === 1}
                    >
                      上一页
                    </Button>
                    <span className="text-sm text-gray-600">
                      {currentChunkPage} / {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setCurrentChunkPage(
                          Math.min(totalPages, currentChunkPage + 1)
                        )
                      }
                      disabled={currentChunkPage === totalPages}
                    >
                      下一页
                    </Button>
                  </div>
                </div>

                <div className="space-y-4">
                  {currentChunks.map((chunk) => (
                    <Card
                      key={chunk.id}
                      className="p-4 cursor-pointer hover:bg-gray-50 border-l-4 border-l-blue-400"
                      onClick={() => setShowChunkEditDialog(chunk)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge variant="outline">分块 {chunk.id}</Badge>
                            <Badge variant="secondary" className="text-xs">
                              {sliceOperators.find(
                                (op) => op.id === chunk.sliceOperator
                              )?.name || chunk.sliceOperator}
                            </Badge>
                            {chunk.vectorId && (
                              <Badge variant="outline" className="text-xs">
                                <Vector className="w-3 h-3 mr-1" />
                                已向量化
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm leading-relaxed text-gray-700 line-clamp-3">
                            {chunk.content}
                          </p>
                          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                            <span>位置: {chunk.position}</span>
                            <span>Token: {chunk.tokens}</span>
                            {chunk.metadata?.page && (
                              <span>页码: {chunk.metadata.page}</span>
                            )}
                            {chunk.metadata?.section && (
                              <span>章节: {chunk.metadata.section}</span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2 ml-4">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              setShowChunkEditDialog(chunk);
                            }}
                          >
                            <Edit className="w-4 h-4" />
                            编辑
                          </Button>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="vectors" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <Card className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Vector className="w-5 h-5 text-purple-600" />
                      <h4 className="font-medium">向量化状态</h4>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">状态:</span>
                        <Badge
                          variant={getStatusBadgeVariant(
                            selectedFile.vectorizationStatus || "pending"
                          )}
                        >
                          {getStatusLabel(
                            selectedFile.vectorizationStatus || "pending"
                          )}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">向量维度:</span>
                        <span className="font-medium">
                          {selectedKB?.config.vectorDimension}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">向量数量:</span>
                        <span className="font-medium">
                          {selectedFile.chunkCount}
                        </span>
                      </div>
                    </div>
                  </Card>
                  <Card className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Server className="w-5 h-5 text-blue-600" />
                      <h4 className="font-medium">存储信息</h4>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">
                          向量数据库:
                        </span>
                        <span className="font-medium">
                          {
                            vectorDatabases.find(
                              (db) => db.id === selectedKB?.vectorDatabase
                            )?.name
                          }
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">嵌入模型:</span>
                        <span className="font-medium">
                          {selectedKB?.config.embeddingModel}
                        </span>
                      </div>
                    </div>
                  </Card>
                </div>
                {selectedFile.vectorizationStatus === "processing" && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>向量化进度</span>
                      <span>{selectedFile.progress}%</span>
                    </div>
                    <Progress value={selectedFile.progress} className="h-2" />
                  </div>
                )}
              </TabsContent>

              <TabsContent value="metadata" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>文件类型</Label>
                    <Input value={selectedFile.type} readOnly />
                  </div>
                  <div>
                    <Label>文件大小</Label>
                    <Input value={selectedFile.size} readOnly />
                  </div>
                  <div>
                    <Label>分块数量</Label>
                    <Input value={selectedFile.chunkCount} readOnly />
                  </div>
                  <div>
                    <Label>上传时间</Label>
                    <Input value={selectedFile.uploadedAt} readOnly />
                  </div>
                  <div>
                    <Label>数据源</Label>
                    <Input
                      value={
                        selectedFile.source === "upload"
                          ? "上传文件"
                          : "数据集文件"
                      }
                      readOnly
                    />
                  </div>
                  {selectedFile.datasetId && (
                    <div>
                      <Label>数据集ID</Label>
                      <Input value={selectedFile.datasetId} readOnly />
                    </div>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="processing" className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>文件上传完成</span>
                    <span className="text-gray-500 ml-auto">
                      2024-01-22 10:30
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>文本提取完成</span>
                    <span className="text-gray-500 ml-auto">
                      2024-01-22 10:32
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>切片算子处理完成</span>
                    <span className="text-gray-500 ml-auto">
                      2024-01-22 10:35
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>文档分块完成</span>
                    <span className="text-gray-500 ml-auto">
                      2024-01-22 10:35
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    {selectedFile.vectorizationStatus === "completed" ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : selectedFile.vectorizationStatus === "processing" ? (
                      <Clock className="w-4 h-4 text-blue-500" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-gray-400" />
                    )}
                    <span>
                      向量化处理
                      {selectedFile.vectorizationStatus === "completed"
                        ? "完成"
                        : selectedFile.vectorizationStatus === "processing"
                        ? "中"
                        : "待开始"}
                    </span>
                    <span className="text-gray-500 ml-auto">
                      {selectedFile.vectorizationStatus === "completed"
                        ? "2024-01-22 10:38"
                        : "-"}
                    </span>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Chunk Edit Dialog */}
        {showChunkEditDialog && (
          <Dialog
            open={!!showChunkEditDialog}
            onOpenChange={() => setShowChunkEditDialog(null)}
          >
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>
                  {showChunkEditDialog.id === 0
                    ? "添加新数据索引"
                    : `编辑分块 ${showChunkEditDialog.id}`}
                </DialogTitle>
                <DialogDescription>
                  {showChunkEditDialog.id === 0
                    ? "创建新的数据索引项"
                    : "修改分块内容，支持Chunk或QA模式"}
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4">
                <div>
                  <Label>编辑模式</Label>
                  <div className="flex gap-4 mt-2">
                    <div className="flex items-center space-x-2">
                      <input
                        type="radio"
                        id="chunk-edit-mode"
                        name="edit-mode"
                        checked={editingChunkMode === "chunk"}
                        onChange={() => setEditingChunkMode("chunk")}
                        className="w-4 h-4 text-blue-600"
                      />
                      <Label htmlFor="chunk-edit-mode">Chunk 模式</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input
                        type="radio"
                        id="qa-edit-mode"
                        name="edit-mode"
                        checked={editingChunkMode === "qa"}
                        onChange={() => setEditingChunkMode("qa")}
                        className="w-4 h-4 text-blue-600"
                      />
                      <Label htmlFor="qa-edit-mode">QA 模式</Label>
                    </div>
                  </div>
                </div>

                {editingChunkMode === "chunk" ? (
                  <div>
                    <Label>分块内容</Label>
                    <Textarea
                      value={chunkEditContent || showChunkEditDialog.content}
                      onChange={(e) => setChunkEditContent(e.target.value)}
                      rows={8}
                      placeholder="输入分块内容..."
                      className="mt-2"
                    />
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <Label>问题</Label>
                      <Textarea
                        value={qaQuestion}
                        onChange={(e) => setQaQuestion(e.target.value)}
                        rows={3}
                        placeholder="输入问题..."
                        className="mt-2"
                      />
                    </div>
                    <div>
                      <Label>答案</Label>
                      <Textarea
                        value={qaAnswer}
                        onChange={(e) => setQaAnswer(e.target.value)}
                        rows={5}
                        placeholder="输入答案..."
                        className="mt-2"
                      />
                    </div>
                  </div>
                )}

                {showChunkEditDialog.id !== 0 && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>位置</Label>
                      <Input
                        value={showChunkEditDialog.position}
                        readOnly
                        className="bg-gray-50"
                      />
                    </div>
                    <div>
                      <Label>Token数量</Label>
                      <Input
                        value={showChunkEditDialog.tokens}
                        readOnly
                        className="bg-gray-50"
                      />
                    </div>
                  </div>
                )}
              </div>

              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setShowChunkEditDialog(null)}
                >
                  取消
                </Button>
                <Button
                  onClick={handleSaveChunkEdit}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <Save className="w-4 h-4 mr-2" />
                  确认更新
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}

        {/* Slice Trace Dialog */}
        {showSliceTraceDialog && (
          <Dialog
            open={!!showSliceTraceDialog}
            onOpenChange={() => setShowSliceTraceDialog(null)}
          >
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>知识切片回溯</DialogTitle>
                <DialogDescription>
                  查看分块 {showSliceTraceDialog} 的切片处理历史和算子应用过程
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium mb-3">切片处理流程</h4>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
                        1
                      </div>
                      <div className="flex-1">
                        <p className="font-medium">原始文档导入</p>
                        <p className="text-sm text-gray-600">
                          文档: {selectedFile.name}
                        </p>
                      </div>
                      <Badge variant="outline">完成</Badge>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
                        2
                      </div>
                      <div className="flex-1">
                        <p className="font-medium">语义分割算子</p>
                        <p className="text-sm text-gray-600">
                          基于语义相似度智能分割，阈值: 0.7
                        </p>
                      </div>
                      <Badge variant="outline">完成</Badge>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
                        3
                      </div>
                      <div className="flex-1">
                        <p className="font-medium">段落分割算子</p>
                        <p className="text-sm text-gray-600">
                          按段落边界进一步细分
                        </p>
                      </div>
                      <Badge variant="outline">完成</Badge>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center text-sm font-medium">
                        4
                      </div>
                      <div className="flex-1">
                        <p className="font-medium">向量化处理</p>
                        <p className="text-sm text-gray-600">
                          使用 {selectedKB?.config.embeddingModel} 生成向量
                        </p>
                      </div>
                      <Badge
                        variant={
                          selectedFile.vectorizationStatus === "completed"
                            ? "outline"
                            : "secondary"
                        }
                      >
                        {selectedFile.vectorizationStatus === "completed"
                          ? "完成"
                          : "处理中"}
                      </Badge>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <Card className="p-4">
                    <h4 className="font-medium mb-2">分块信息</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">分块ID:</span>
                        <span>{showSliceTraceDialog}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">父分块:</span>
                        <span>
                          {mockChunks.find((c) => c.id === showSliceTraceDialog)
                            ?.parentChunkId || "无"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Token数:</span>
                        <span>
                          {
                            mockChunks.find(
                              (c) => c.id === showSliceTraceDialog
                            )?.tokens
                          }
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">创建时间:</span>
                        <span>
                          {
                            mockChunks.find(
                              (c) => c.id === showSliceTraceDialog
                            )?.createdAt
                          }
                        </span>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-4">
                    <h4 className="font-medium mb-2">向量信息</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">向量ID:</span>
                        <span className="font-mono text-xs">
                          {
                            mockChunks.find(
                              (c) => c.id === showSliceTraceDialog
                            )?.vectorId
                          }
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">向量维度:</span>
                        <span>{selectedKB?.config.vectorDimension}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">相似度:</span>
                        <span>
                          {
                            mockChunks.find(
                              (c) => c.id === showSliceTraceDialog
                            )?.similarity
                          }
                        </span>
                      </div>
                    </div>
                  </Card>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}

        {chunkDetailModal && (
          <Dialog
            open={!!chunkDetailModal}
            onOpenChange={() => setChunkDetailModal(null)}
          >
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>
                  分块详细信息 - 分块 {chunkDetailModal}
                </DialogTitle>
                <DialogDescription>
                  查看分块的完整内容、元数据和关联信息
                </DialogDescription>
              </DialogHeader>

              <Tabs defaultValue="content">
                <TabsList>
                  <TabsTrigger value="content">内容详情</TabsTrigger>
                  <TabsTrigger value="metadata">元数据</TabsTrigger>
                  <TabsTrigger value="qa">Q&A对</TabsTrigger>
                  <TabsTrigger value="trace">切片回溯</TabsTrigger>
                </TabsList>

                <TabsContent value="content" className="space-y-4">
                  <div>
                    <Label>分块内容</Label>
                    <Textarea
                      value={
                        mockChunks.find((c) => c.id === chunkDetailModal)
                          ?.content || ""
                      }
                      rows={8}
                      readOnly
                      className="mt-2"
                    />
                  </div>
                </TabsContent>

                <TabsContent value="metadata" className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>位置</Label>
                      <Input
                        value={
                          mockChunks.find((c) => c.id === chunkDetailModal)
                            ?.position || ""
                        }
                        readOnly
                      />
                    </div>
                    <div>
                      <Label>Token数量</Label>
                      <Input
                        value={
                          mockChunks.find((c) => c.id === chunkDetailModal)
                            ?.tokens || ""
                        }
                        readOnly
                      />
                    </div>
                    <div>
                      <Label>相似度</Label>
                      <Input
                        value={
                          mockChunks.find((c) => c.id === chunkDetailModal)
                            ?.similarity || ""
                        }
                        readOnly
                      />
                    </div>
                    <div>
                      <Label>向量维度</Label>
                      <Input
                        value={
                          mockChunks.find((c) => c.id === chunkDetailModal)
                            ?.embedding?.length || ""
                        }
                        readOnly
                      />
                    </div>
                    <div>
                      <Label>创建时间</Label>
                      <Input
                        value={
                          mockChunks.find((c) => c.id === chunkDetailModal)
                            ?.createdAt || ""
                        }
                        readOnly
                      />
                    </div>
                    <div>
                      <Label>更新时间</Label>
                      <Input
                        value={
                          mockChunks.find((c) => c.id === chunkDetailModal)
                            ?.updatedAt || ""
                        }
                        readOnly
                      />
                    </div>
                    <div>
                      <Label>向量ID</Label>
                      <Input
                        value={
                          mockChunks.find((c) => c.id === chunkDetailModal)
                            ?.vectorId || ""
                        }
                        readOnly
                      />
                    </div>
                    <div>
                      <Label>切片算子</Label>
                      <Input
                        value={
                          mockChunks.find((c) => c.id === chunkDetailModal)
                            ?.sliceOperator || ""
                        }
                        readOnly
                      />
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="qa" className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label>关联的问答对</Label>
                    <Button size="sm">
                      <Plus className="w-4 h-4 mr-1" />
                      添加Q&A
                    </Button>
                  </div>
                  <div className="space-y-3">
                    {mockQAPairs.map((qa) => (
                      <Card key={qa.id} className="p-4">
                        <div className="space-y-2">
                          <div>
                            <Label className="text-sm font-medium text-blue-600">
                              问题 {qa.id}
                            </Label>
                            <p className="text-sm mt-1">{qa.question}</p>
                          </div>
                          <div>
                            <Label className="text-sm font-medium text-green-600">
                              答案
                            </Label>
                            <p className="text-sm mt-1">{qa.answer}</p>
                          </div>
                          <div className="flex justify-end gap-2">
                            <Button variant="ghost" size="sm">
                              <Edit className="w-3 h-3 mr-1" />
                              编辑
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-600"
                            >
                              <Trash2 className="w-3 h-3 mr-1" />
                              删除
                            </Button>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="trace" className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                      <FileText className="w-5 h-5 text-blue-600" />
                      <div className="flex-1">
                        <p className="font-medium">原始文档</p>
                        <p className="text-sm text-gray-600">
                          {selectedFile.name}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                      <Scissors className="w-5 h-5 text-green-600" />
                      <div className="flex-1">
                        <p className="font-medium">切片算子处理</p>
                        <p className="text-sm text-gray-600">
                          应用算子:{" "}
                          {
                            sliceOperators.find(
                              (op) =>
                                op.id ===
                                mockChunks.find(
                                  (c) => c.id === chunkDetailModal
                                )?.sliceOperator
                            )?.name
                          }
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg">
                      <Vector className="w-5 h-5 text-purple-600" />
                      <div className="flex-1">
                        <p className="font-medium">向量化处理</p>
                        <p className="text-sm text-gray-600">
                          生成 {selectedKB?.config.vectorDimension} 维向量
                        </p>
                      </div>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </DialogContent>
          </Dialog>
        )}
      </div>
    );
  }

  // Detail view
  if (currentView === "detail" && selectedKB) {
    return (
      <div className="space-y-6">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <button
            onClick={() => setCurrentView("list")}
            className="hover:text-blue-600"
          >
            知识库
          </button>
          <ChevronRight className="w-4 h-4" />
          <span>{selectedKB.name}</span>
        </div>

        {/* Knowledge Base Header */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4 flex-1">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg">
                  {selectedKB.type === "structured" ? (
                    <Database className="w-8 h-8" />
                  ) : (
                    <BookOpen className="w-8 h-8" />
                  )}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h1 className="text-2xl font-bold text-gray-900">
                      {selectedKB.name}
                    </h1>
                    <Badge
                      variant={getStatusBadgeVariant(selectedKB.status)}
                      className="text-sm"
                    >
                      {getStatusIcon(selectedKB.status)}
                      <span className="ml-1">
                        {getStatusLabel(selectedKB.status)}
                      </span>
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                    <span>v1.0.0</span>
                    <span>•</span>
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      <span>创建于 {selectedKB.createdAt}</span>
                    </div>
                    <span>•</span>
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      <span>更新于 {selectedKB.lastUpdated}</span>
                    </div>
                  </div>
                  <p className="text-gray-700 mb-4">{selectedKB.description}</p>
                  <div className="flex items-center gap-6 text-sm">
                    <div className="flex items-center gap-1">
                      <File className="w-4 h-4 text-gray-400" />
                      <span>{selectedKB.fileCount} 个文件</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Layers className="w-4 h-4 text-gray-400" />
                      <span>
                        {selectedKB.chunkCount.toLocaleString()} 个分块
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Vector className="w-4 h-4 text-gray-400" />
                      <span>
                        {selectedKB.vectorCount.toLocaleString()} 个向量
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Database className="w-4 h-4 text-gray-400" />
                      <span>{selectedKB.size}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setEditForm(selectedKB);
                    setCurrentView("config");
                  }}
                >
                  <Edit className="w-4 h-4 mr-2" />
                  修改参数配置
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowVectorizationDialog(true)}
                >
                  <Vector className="w-4 h-4 mr-2" />
                  向量化管理
                </Button>
                {selectedKB.status === "error" && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-orange-600 border-orange-200 bg-transparent"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    重试处理
                  </Button>
                )}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm">
                      <MoreHorizontal className="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem>
                      <Download className="w-4 h-4 mr-2" />
                      导出知识库
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Settings className="w-4 h-4 mr-2" />
                      配置设置
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={() => handleDeleteKB(selectedKB)}
                      className="text-red-600"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      删除知识库
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tab Navigation */}
        <Card>
          <CardContent className="p-6">
            {/* Files Section */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  文件列表
                </h3>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <Input
                      placeholder="搜索文件名..."
                      value={fileSearchQuery}
                      onChange={(e) => setFileSearchQuery(e.target.value)}
                      className="pl-10 w-64"
                    />
                  </div>
                  <Select
                    value={fileStatusFilter}
                    onValueChange={setFileStatusFilter}
                  >
                    <SelectTrigger className="w-32">
                      <SelectValue placeholder="状态筛选" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部状态</SelectItem>
                      <SelectItem value="completed">已完成</SelectItem>
                      <SelectItem value="processing">处理中</SelectItem>
                      <SelectItem value="vectorizing">向量化中</SelectItem>
                      <SelectItem value="error">错误</SelectItem>
                      <SelectItem value="disabled">已禁用</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button size="sm">
                    <Plus className="w-4 h-4 mr-1" />
                    添加文件
                  </Button>
                </div>
              </div>

              {/* Files Table */}
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="text-left p-4 font-medium text-gray-900">
                        文件名
                      </th>
                      <th className="text-left p-4 font-medium text-gray-900">
                        来源
                      </th>
                      <th className="text-left p-4 font-medium text-gray-900">
                        格式
                      </th>
                      <th className="text-left p-4 font-medium text-gray-900">
                        大小
                      </th>
                      <th className="text-left p-4 font-medium text-gray-900">
                        分块数
                      </th>
                      <th className="text-left p-4 font-medium text-gray-900">
                        向量化状态
                      </th>
                      <th className="text-left p-4 font-medium text-gray-900">
                        上传时间
                      </th>
                      <th className="text-right p-4 font-medium text-gray-900">
                        操作
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {filteredFiles.map((file) => (
                      <tr
                        key={file.id}
                        className="hover:bg-gray-50 transition-colors"
                      >
                        <td className="p-4">
                          <div className="flex items-center gap-3">
                            <File className="w-4 h-4 text-gray-400" />
                            <span className="font-medium text-gray-900">
                              {file.name}
                            </span>
                          </div>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-xs">
                              {file.source === "upload" ? "上传" : "数据集"}
                            </Badge>
                            {file.datasetId && (
                              <span className="text-xs text-gray-500">
                                ({file.datasetId})
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="p-4">
                          <Badge variant="outline" className="uppercase">
                            {file.type}
                          </Badge>
                        </td>
                        <td className="p-4">
                          <span className="text-gray-700">{file.size}</span>
                        </td>
                        <td className="p-4">
                          <span className="font-medium text-gray-900">
                            {file.chunkCount}
                          </span>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <Badge
                              variant={getStatusBadgeVariant(
                                file.vectorizationStatus || "pending"
                              )}
                            >
                              {getStatusIcon(
                                file.vectorizationStatus || "pending"
                              )}
                              <span className="ml-1">
                                {getStatusLabel(
                                  file.vectorizationStatus || "pending"
                                )}
                              </span>
                            </Badge>
                            {file.vectorizationStatus === "processing" && (
                              <div className="w-16">
                                <Progress
                                  value={file.progress}
                                  className="h-1"
                                />
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="p-4">
                          <span className="text-sm text-gray-600">
                            {file.uploadedAt}
                          </span>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleFileSelect(file)}
                              className="text-blue-600 hover:text-blue-700"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            {file.source === "upload" && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-green-600 hover:text-green-700"
                              >
                                <RefreshCw className="w-4 h-4" />
                              </Button>
                            )}
                            {file.vectorizationStatus !== "completed" && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() =>
                                  handleStartVectorization(file.id)
                                }
                                className="text-purple-600 hover:text-purple-700"
                              >
                                <Vector className="w-4 h-4" />
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteFile(file)}
                              className="text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {filteredFiles.length === 0 && (
                  <div className="text-center py-12">
                    <File className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      没有找到文件
                    </h3>
                    <p className="text-gray-500 mb-4">
                      尝试调整搜索条件或添加新文件
                    </p>
                    <Button variant="outline">
                      <Upload className="w-4 h-4 mr-2" />
                      添加文件
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Vectorization Dialog */}
        {showVectorizationDialog && (
          <Dialog
            open={showVectorizationDialog}
            onOpenChange={setShowVectorizationDialog}
          >
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>向量化管理</DialogTitle>
                <DialogDescription>
                  管理知识库的向量化操作，包括批量处理和重新向量化
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <Card className="p-4">
                    <h4 className="font-medium mb-2">当前状态</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>已向量化文件:</span>
                        <span>
                          {
                            selectedKB.files.filter(
                              (f) => f.vectorizationStatus === "completed"
                            ).length
                          }
                          /{selectedKB.files.length}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>向量总数:</span>
                        <span>{selectedKB.vectorCount.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>存储大小:</span>
                        <span>{selectedKB.size}</span>
                      </div>
                    </div>
                  </Card>
                  <Card className="p-4">
                    <h4 className="font-medium mb-2">操作选项</h4>
                    <div className="space-y-2">
                      <Button
                        className="w-full"
                        onClick={() => handleStartVectorization()}
                      >
                        <Zap className="w-4 h-4 mr-2" />
                        批量向量化
                      </Button>
                      <Button
                        variant="outline"
                        className="w-full bg-transparent"
                      >
                        <RefreshCw className="w-4 h-4 mr-2" />
                        重新向量化全部
                      </Button>
                      <Button
                        variant="outline"
                        className="w-full bg-transparent"
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        清空向量数据
                      </Button>
                    </div>
                  </Card>
                </div>

                <div>
                  <h4 className="font-medium mb-3">文件向量化状态</h4>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {selectedKB.files.map((file) => (
                      <div
                        key={file.id}
                        className="flex items-center justify-between p-3 border rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <File className="w-4 h-4 text-gray-400" />
                          <div>
                            <p className="font-medium text-sm">{file.name}</p>
                            <p className="text-xs text-gray-500">
                              {file.chunkCount} 个分块
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={getStatusBadgeVariant(
                              file.vectorizationStatus || "pending"
                            )}
                            className="text-xs"
                          >
                            {getStatusLabel(
                              file.vectorizationStatus || "pending"
                            )}
                          </Badge>
                          {file.vectorizationStatus !== "completed" && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleStartVectorization(file.id)}
                            >
                              <Vector className="w-3 h-3" />
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setShowVectorizationDialog(false)}
                >
                  关闭
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}

        {/* Edit File Dialog */}
        {showEditFileDialog && (
          <Dialog
            open={!!showEditFileDialog}
            onOpenChange={() => setShowEditFileDialog(null)}
          >
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>编辑文件</DialogTitle>
                <DialogDescription>
                  修改文件配置或更新文件内容
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>文件名</Label>
                    <Input value={showEditFileDialog.name} readOnly />
                  </div>
                  <div>
                    <Label>文件来源</Label>
                    <Input
                      value={
                        showEditFileDialog.source === "upload"
                          ? "上传文件"
                          : "数据集文件"
                      }
                      readOnly
                    />
                  </div>
                </div>

                {showEditFileDialog.source === "upload" ? (
                  <div className="space-y-3">
                    <Label>更新文件</Label>
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                      <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                      <p className="text-sm text-gray-600">
                        拖拽或点击上传新版本文件
                      </p>
                      <Button variant="outline" className="mt-2 bg-transparent">
                        选择文件
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <Label>数据集文件管理</Label>
                    <div className="p-4 border rounded-lg bg-gray-50">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">
                          当前数据集: {showEditFileDialog.datasetId}
                        </span>
                        <Button variant="outline" size="sm">
                          <RefreshCw className="w-4 h-4 mr-1" />
                          更新数据集文件
                        </Button>
                      </div>
                      <p className="text-xs text-gray-600">
                        此文件来自数据集，可以选择更新数据集中的对应文件或切换到其他数据集文件
                      </p>
                    </div>
                  </div>
                )}

                <div className="space-y-3">
                  <Label>处理选项</Label>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox id="reprocess" />
                      <Label htmlFor="reprocess" className="text-sm">
                        更新后重新处理分块
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox id="revectorize" />
                      <Label htmlFor="revectorize" className="text-sm">
                        重新生成向量
                      </Label>
                    </div>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setShowEditFileDialog(null)}
                >
                  取消
                </Button>
                <Button onClick={() => setShowEditFileDialog(null)}>
                  <Save className="w-4 h-4 mr-2" />
                  保存更改
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </div>
    );
  }

  // Main list view
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">知识库管理</h1>
          <p className="text-gray-600 mt-1">
            构建和管理RAG知识库，支持结构化和非结构化数据处理
          </p>
        </div>
        <Button
          onClick={() => setCurrentView("create")}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          创建知识库
        </Button>
      </div>

      {/* Search and Controls */}
      <SearchControls
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        searchPlaceholder="搜索知识库..."
        filters={filterOptions}
        selectedFilters={{
          type: typeFilter === "all" ? [] : [typeFilter],
          status: statusFilter === "all" ? [] : [statusFilter],
        }}
        onFiltersChange={(filters) => {
          setTypeFilter(filters.type?.[0] || "all");
          setStatusFilter(filters.status?.[0] || "all");
        }}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSortChange={(field, order) => {
          setSortBy(field);
          setSortOrder(order);
        }}
        sortOptions={sortOptions}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />

      {viewMode === "card" ? (
        <div className="grid gap-6">
          {filteredData.map((kb) => (
            <Card
              key={kb.id}
              className="group hover:shadow-lg transition-all duration-200 border-l-4 border-l-blue-500"
            >
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4 flex-1">
                    <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl text-white shadow-lg">
                      {kb.type === "structured" ? (
                        <Database className="w-6 h-6" />
                      ) : (
                        <BookOpen className="w-6 h-6" />
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 truncate">
                          {kb.name}
                        </h3>
                        <Badge
                          variant={getStatusBadgeVariant(kb.status)}
                          className="shrink-0"
                        >
                          {getStatusIcon(kb.status)}
                          <span className="ml-1">
                            {getStatusLabel(kb.status)}
                          </span>
                        </Badge>
                        <Badge variant="outline" className="shrink-0">
                          {kb.type === "structured" ? "结构化" : "非结构化"}
                        </Badge>
                      </div>

                      <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                        {kb.description}
                      </p>

                      {(kb.status === "processing" ||
                        kb.status === "vectorizing") && (
                        <div className="mb-4">
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600">
                              {kb.status === "processing"
                                ? "处理进度"
                                : "向量化进度"}
                            </span>
                            <span className="font-medium text-blue-600">
                              {kb.progress}%
                            </span>
                          </div>
                          <Progress value={kb.progress} className="h-2" />
                        </div>
                      )}

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div className="flex items-center gap-2">
                          <File className="w-4 h-4 text-gray-400" />
                          <span className="text-gray-600">文件:</span>
                          <span className="font-semibold text-gray-900">
                            {kb.fileCount}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Layers className="w-4 h-4 text-gray-400" />
                          <span className="text-gray-600">分块:</span>
                          <span className="font-semibold text-gray-900">
                            {kb.chunkCount.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Vector className="w-4 h-4 text-gray-400" />
                          <span className="text-gray-600">向量:</span>
                          <span className="font-semibold text-gray-900">
                            {kb.vectorCount.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Database className="w-4 h-4 text-gray-400" />
                          <span className="text-gray-600">大小:</span>
                          <span className="font-semibold text-gray-900">
                            {kb.size}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleKBSelect(kb)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Eye className="w-4 h-4 mr-1" />
                      查看
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0"
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleKBSelect(kb)}>
                          <Eye className="w-4 h-4 mr-2" />
                          查看详情
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => {
                            setEditForm(kb);
                            setCurrentView("config");
                          }}
                        >
                          <Edit className="w-4 h-4 mr-2" />
                          修改参数配置
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Vector className="w-4 h-4 mr-2" />
                          向量化管理
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Download className="w-4 h-4 mr-2" />
                          导出数据
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => handleDeleteKB(kb)}
                          className="text-red-600"
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          删除知识库
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          {filteredData.length === 0 && (
            <div className="text-center py-16">
              <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <BookOpen className="w-12 h-12 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                没有找到知识库
              </h3>
              <p className="text-gray-500 mb-6">
                尝试调整筛选条件或创建新的知识库
              </p>
              <Button
                onClick={() => setCurrentView("create")}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                创建知识库
              </Button>
            </div>
          )}
        </div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="text-left p-4 font-medium text-gray-900">
                      知识库
                    </th>
                    <th className="text-left p-4 font-medium text-gray-900">
                      类型
                    </th>
                    <th className="text-left p-4 font-medium text-gray-900">
                      状态
                    </th>
                    <th className="text-left p-4 font-medium text-gray-900">
                      向量数据库
                    </th>
                    <th className="text-left p-4 font-medium text-gray-900">
                      文件数
                    </th>
                    <th className="text-left p-4 font-medium text-gray-900">
                      向量数
                    </th>
                    <th className="text-left p-4 font-medium text-gray-900">
                      大小
                    </th>
                    <th className="text-left p-4 font-medium text-gray-900">
                      创建时间
                    </th>
                    <th className="text-right p-4 font-medium text-gray-900">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredData.map((kb) => (
                    <tr
                      key={kb.id}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg text-white">
                            {kb.type === "structured" ? (
                              <Database className="w-4 h-4" />
                            ) : (
                              <BookOpen className="w-4 h-4" />
                            )}
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="font-medium text-gray-900 truncate">
                              {kb.name}
                            </p>
                            <p className="text-sm text-gray-500 truncate">
                              {kb.description}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="p-4">
                        <Badge variant="outline">
                          {kb.type === "structured" ? "结构化" : "非结构化"}
                        </Badge>
                      </td>
                      <td className="p-4">
                        <Badge variant={getStatusBadgeVariant(kb.status)}>
                          {getStatusIcon(kb.status)}
                          <span className="ml-1">
                            {getStatusLabel(kb.status)}
                          </span>
                        </Badge>
                      </td>
                      <td className="p-4">
                        <span className="text-sm">
                          {
                            vectorDatabases.find(
                              (db) => db.id === kb.vectorDatabase
                            )?.name
                          }
                        </span>
                      </td>
                      <td className="p-4">
                        <span className="font-medium">{kb.fileCount}</span>
                      </td>
                      <td className="p-4">
                        <span className="font-medium">
                          {kb.vectorCount.toLocaleString()}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className="font-medium">{kb.size}</span>
                      </td>
                      <td className="p-4">
                        <span className="text-sm text-gray-600">
                          {kb.createdAt}
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleKBSelect(kb)}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-8 w-8 p-0"
                              >
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={() => handleKBSelect(kb)}
                              >
                                <Eye className="w-4 h-4 mr-2" />
                                查看详情
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => {
                                  setEditForm(kb);
                                  setCurrentView("config");
                                }}
                              >
                                <Edit className="w-4 h-4 mr-2" />
                                修改参数配置
                              </DropdownMenuItem>
                              <DropdownMenuItem>
                                <Vector className="w-4 h-4 mr-2" />
                                向量化管理
                              </DropdownMenuItem>
                              <DropdownMenuItem>
                                <Download className="w-4 h-4 mr-2" />
                                导出数据
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={() => handleDeleteKB(kb)}
                                className="text-red-600"
                              >
                                <Trash2 className="w-4 h-4 mr-2" />
                                删除知识库
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {filteredData.length === 0 && (
                <div className="text-center py-16">
                  <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <BookOpen className="w-12 h-12 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    没有找到知识库
                  </h3>
                  <p className="text-gray-500 mb-6">
                    尝试调整筛选条件或创建新的知识库
                  </p>
                  <Button
                    onClick={() => setCurrentView("create")}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    创建知识库
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
