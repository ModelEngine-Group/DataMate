import { useState } from "react";
import { Card, Button, Badge, Table, Dropdown, Menu } from "antd";
import { SearchControls } from "@/components/SearchControls";
import {
  BookOpen,
  Plus,
  Eye,
  Upload,
  Database,
  Edit,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  MoreHorizontal,
  Trash2,
  Download,
  VideoIcon as Vector,
} from "lucide-react";
import { mockKnowledgeBases, vectorDatabases } from "@/mock/knowledgeBase";
import { useNavigate } from "react-router";
import CardView from "@/components/CardView";

export default function KnowledgeGenerationPage() {
  const navigate = useNavigate();
  const [knowledgeBases, setKnowledgeBases] =
    useState<KnowledgeBase[]>(mockKnowledgeBases);
  const [typeFilter, setTypeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState<
    "name" | "size" | "fileCount" | "createdAt"
  >("createdAt");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [viewMode, setViewMode] = useState<"card" | "list">("card");
  const [searchTerm, setSearchTerm] = useState("");

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

  const handleDeleteKB = (kb: KnowledgeBase) => {
    if (confirm(`确定要删除知识库 "${kb.name}" 吗？此操作不可撤销。`)) {
      setKnowledgeBases((prev) => prev.filter((k) => k.id !== kb.id));
    }
  };

  const columns = [
    {
      title: "知识库",
      dataIndex: "name",
      key: "name",
      render: (_: any, kb: KnowledgeBase) => (
        <div
          className="flex items-center gap-3 cursor-pointer"
          onClick={() => navigate(`/data/knowledge-generation/detail/${kb.id}`)}
        >
          <div className="p-2 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg text-white">
            {kb.type === "structured" ? (
              <Database className="w-4 h-4" />
            ) : (
              <BookOpen className="w-4 h-4" />
            )}
          </div>
          <div className="min-w-0 flex-1">
            <p className="font-medium text-gray-900 truncate">{kb.name}</p>
            <p className="text-sm text-gray-500 truncate">{kb.description}</p>
          </div>
        </div>
      ),
    },
    {
      title: "类型",
      dataIndex: "type",
      key: "type",
      render: (type: string) => (
        <Badge variant="outline">
          {type === "structured" ? "结构化" : "非结构化"}
        </Badge>
      ),
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (status: string) => (
        <Badge variant={getStatusBadgeVariant(status)}>
          {getStatusIcon(status)}
          <span className="ml-1">{getStatusLabel(status)}</span>
        </Badge>
      ),
    },
    {
      title: "向量数据库",
      dataIndex: "vectorDatabase",
      key: "vectorDatabase",
      render: (vectorDatabase: string) => (
        <span className="text-sm">
          {vectorDatabases.find((db) => db.id === vectorDatabase)?.name}
        </span>
      ),
    },
    {
      title: "文件数",
      dataIndex: "fileCount",
      key: "fileCount",
      render: (fileCount: number) => (
        <span className="font-medium">{fileCount}</span>
      ),
    },
    {
      title: "向量数",
      dataIndex: "vectorCount",
      key: "vectorCount",
      render: (vectorCount: number) => (
        <span className="font-medium">{vectorCount?.toLocaleString()}</span>
      ),
    },
    {
      title: "大小",
      dataIndex: "size",
      key: "size",
      render: (size: string) => <span className="font-medium">{size}</span>,
    },
    {
      title: "创建时间",
      dataIndex: "createdAt",
      key: "createdAt",
      render: (createdAt: string) => (
        <span className="text-sm text-gray-600">{createdAt}</span>
      ),
    },
    {
      title: "操作",
      key: "actions",
      align: "right" as const,
      render: (_: any, kb: KnowledgeBase) => (
        <div className="flex items-center justify-end gap-2">
          <Button
            type="text"
            size="small"
            onClick={() =>
              navigate(`/data/knowledge-generation/detail/${kb.id}`)
            }
          >
            <Eye className="w-4 h-4" />
          </Button>
          <Dropdown
            trigger={["click"]}
            overlay={
              <Menu>
                <Menu.Item
                  key="view"
                  onClick={() =>
                    navigate(`/data/knowledge-generation/detail/${kb.id}`)
                  }
                >
                  <Eye className="w-4 h-4 mr-2" />
                  查看详情
                </Menu.Item>
                <Menu.Item key="vector">
                  <Vector className="w-4 h-4 mr-2" />
                  向量化管理
                </Menu.Item>
                <Menu.Item key="download">
                  <Download className="w-4 h-4 mr-2" />
                  导出数据
                </Menu.Item>
                <Menu.Divider />
                <Menu.Item
                  key="delete"
                  onClick={() => handleDeleteKB(kb)}
                  danger
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  删除知识库
                </Menu.Item>
              </Menu>
            }
          >
            <Button type="text" size="small" className="h-8 w-8 p-0">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </Dropdown>
        </div>
      ),
    },
  ];

  // Main list view
  return (
    <div className="">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">知识库管理</h1>
        <Button
          type="primary"
          onClick={() => navigate("/data/knowledge-generation/create")}
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
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />

      {viewMode === "card" ? (
        <CardView
          data={filteredData.map((kb) => ({
            id: kb.id,
            name: kb.name,
            type: kb.type,
            icon:
              kb.type === "structured" ? (
                <Database className="w-6 h-6 text-white-100" />
              ) : (
                <BookOpen className="w-6 h-6 text-white-100" />
              ),
            iconColor: "",
            status: {
              label: getStatusLabel(kb.status),
              icon: getStatusIcon(kb.status),
              color:
                kb.status === "ready" || kb.status === "completed"
                  ? "green"
                  : kb.status === "processing" || kb.status === "vectorizing"
                  ? "blue"
                  : kb.status === "importing"
                  ? "orange"
                  : kb.status === "error"
                  ? "red"
                  : "gray",
            },
            description: kb.description,
            tags: [],
            statistics: [
              { label: "文件", value: kb.fileCount },
              { label: "分块", value: kb.chunkCount },
              { label: "向量", value: kb.vectorCount },
              { label: "大小", value: kb.size },
            ],
            lastModified: kb.lastUpdated || kb.createdAt,
          }))}
          operations={[
            {
              key: "view",
              label: "查看详情",
              icon: <Eye className="w-4 h-4 mr-2" />,
              onClick: (kb) =>
                navigate(`/data/knowledge-generation/detail/${kb.id}`),
            },
            {
              key: "edit",
              label: "修改参数配置",
              icon: <Edit className="w-4 h-4 mr-2" />,
              onClick: (item) => {},
            },
            {
              key: "vector",
              label: "向量化管理",
              icon: <Vector className="w-4 h-4 mr-2" />,
            },
            {
              key: "download",
              label: "导出数据",
              icon: <Download className="w-4 h-4 mr-2" />,
            },
            {
              key: "delete",
              label: "删除知识库",
              icon: <Trash2 className="w-4 h-4 mr-2" />,
              onClick: (item) =>
                handleDeleteKB(knowledgeBases.find((kb) => kb.id === item.id)!),
            },
          ]}
          onView={(item) =>
            navigate(`/data/knowledge-generation/detail/${item.id}`)
          }
        />
      ) : (
        <Card>
          <Table
            scroll={{ x: "max-content" }}
            columns={columns}
            dataSource={filteredData}
            rowKey="id"
            pagination={false}
            locale={{
              emptyText: (
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
                    onClick={() => navigate("/knowledge-generation/create")}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    创建知识库
                  </Button>
                </div>
              ),
            }}
          />
        </Card>
      )}
    </div>
  );
}
