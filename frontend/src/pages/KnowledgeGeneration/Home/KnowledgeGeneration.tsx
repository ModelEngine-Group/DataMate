import { useState } from "react";
import { Card, Button, Badge, Table, Dropdown } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { SearchControls } from "@/components/SearchControls";
import {
  BookOpen,
  Plus,
  Upload,
  Database,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  MoreHorizontal,
  VideoIcon as Vector,
} from "lucide-react";
import { mockKnowledgeBases, vectorDatabases } from "@/mock/knowledgeBase";
import { useNavigate } from "react-router";
import CardView from "@/components/CardView";
import DevelopmentInProgress from "@/components/DevelopmentInProgress";

export default function KnowledgeGenerationPage() {
  return <DevelopmentInProgress showTime="2025.10.30" />;
  const navigate = useNavigate();
  const [knowledgeBases, setKnowledgeBases] =
    useState<KnowledgeBase[]>(mockKnowledgeBases);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: mockKnowledgeBases.length,
    showSizeChanger: true,
    pageSizeOptions: ["10", "20", "50", "100"],
    onChange: (page: number, pageSize?: number) => {
      setPagination((prev) => ({
        ...prev,
        current: page,
        pageSize: pageSize || prev.pageSize,
      }));
    },
    onShowSizeChange: (current: number, size: number) => {
      setPagination((prev) => ({
        ...prev,
        current: current,
        pageSize: size,
      }));
    },
  });
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
        return <CheckCircle />;
      case "processing":
        return <Clock />;
      case "vectorizing":
        return <Vector />;
      case "importing":
        return <Upload />;
      case "error":
        return <XCircle />;
      case "disabled":
        return <AlertCircle />;
      default:
        return <AlertCircle />;
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case "ready":
      case "completed":
        return "#389e0d"; // green-500
      case "processing":
      case "vectorizing":
      case "importing":
        return "#3b82f6"; // blue-600
      case "error":
        return "#ef4444"; // red-600
      case "disabled":
        return "#6b7280"; // gray-600
      default:
        return "#6b7280"; // gray-600
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
      fixed: "left" as const,
      width: 200,
      render: (_: any, kb: KnowledgeBase) => (
        <div
          className="flex items-center gap-3 cursor-pointer"
          onClick={() => navigate(`/data/knowledge-generation/detail/${kb.id}`)}
        >
          {kb.name}
        </div>
      ),
    },
    {
      title: "类型",
      dataIndex: "type",
      key: "type",
      render: (type: string) => (
        <Badge>{type === "structured" ? "结构化" : "非结构化"}</Badge>
      ),
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (status: string) => (
        <div
          className={`inline-flex items-center text-white px-2 py-1 rounded text-xs`}
          style={{ backgroundColor: getStatusColor(status) }}
        >
          {getStatusIcon(status)}
          <span className="ml-1">{getStatusLabel(status)}</span>
        </div>
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
      fixed: "right" as const,
      render: (_: any, kb: KnowledgeBase) => (
        <div className="flex items-center justify-end gap-2">
          <Dropdown
            trigger={["click"]}
            menu={{
              items: [
                {
                  label: "编辑",
                  key: "edit",
                },
                {
                  label: "导出",
                  key: "download",
                },
                { type: "divider" },
                {
                  label: "删除",
                  key: "delete",
                  danger: true,
                  onClick: () => handleDeleteKB(kb),
                },
              ],
            }}
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
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">知识库管理</h1>
        <Button
          type="primary"
          onClick={() => navigate("/data/knowledge-generation/create")}
          icon={<PlusOutlined className="w-4 h-4" />}
        >
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
            icon: kb.type === "structured" ? <Database /> : <BookOpen />,
            iconColor: "bg-blue-200",
            status: {
              label: getStatusLabel(kb.status),
              icon: getStatusIcon(kb.status),
              color: getStatusColor(kb.status),
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
              key: "edit",
              label: "编辑",
              onClick: (item) => {},
            },
            {
              key: "download",
              label: "导出",
            },
            {
              key: "delete",
              label: "删除",
              onClick: (item) =>
                handleDeleteKB(knowledgeBases.find((kb) => kb.id === item.id)!),
            },
          ]}
          onView={(item) =>
            navigate(`/data/knowledge-generation/detail/${item.id}`)
          }
          pagination={pagination}
        />
      ) : (
        <Card>
          <Table
            scroll={{ x: "max-content" }}
            columns={columns}
            dataSource={filteredData}
            rowKey="id"
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
