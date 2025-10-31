import type React from "react";
import { useEffect, useState } from "react";
import {
  Plus,
  Edit,
  File,
  Trash2,
  Save,
  Layers,
  RefreshCw,
  BookOpen,
  Database,
  MoreHorizontal,
  Upload,
  Zap,
  StarOff,
  CheckCircle,
  VectorSquareIcon,
} from "lucide-react";
import {
  Table,
  Badge,
  Button,
  Progress,
  Input,
  Modal,
  message,
  Card,
  Breadcrumb,
  Checkbox,
  Dropdown,
} from "antd";
import { useNavigate } from "react-router";
import DetailHeader from "@/components/DetailHeader";
import { SearchControls } from "@/components/SearchControls";
import { KnowledgeBaseItem } from "../knowledge-base.model";

const KnowledgeBaseDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBaseItem>(null);
  const [files, setFiles] = useState([]);


  // File table logic
  const handleDeleteFile = (file: KBFile) => {};


  const handleDeleteKB = (kb: KnowledgeBase) => {};

  // 状态 Badge 映射
  function getStatusBadgeVariant(status: string) {
    switch (status) {
      case "completed":
      case "ready":
        return "success";
      case "processing":
      case "vectorizing":
        return "processing";
      case "importing":
        return "warning";
      case "error":
        return "error";
      default:
        return "default";
    }
  }
  function getStatusLabel(status: string) {
    switch (status) {
      case "completed":
      case "ready":
        return "已完成";
      case "processing":
        return "处理中";
      case "vectorizing":
        return "向量化中";
      case "importing":
        return "导入中";
      case "error":
        return "错误";
      case "disabled":
        return "已禁用";
      default:
        return "未知";
    }
  }
  function getStatusIcon(status: string) {
    switch (status) {
      case "completed":
      case "ready":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "processing":
      case "vectorizing":
        return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
      case "importing":
        return <Upload className="w-4 h-4 text-orange-500" />;
      case "error":
        return <Trash2 className="w-4 h-4 text-red-500" />;
      default:
        return <File className="w-4 h-4 text-gray-400" />;
    }
  }

  const fileColumns = [
    {
      title: "文件名",
      dataIndex: "name",
      key: "name",
      filterDropdown: ({
        setSelectedKeys,
        selectedKeys,
        confirm,
        clearFilters,
      }: any) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="搜索文件名"
            value={selectedKeys[0]}
            onChange={(e) =>
              setSelectedKeys(e.target.value ? [e.target.value] : [])
            }
            onPressEnter={confirm}
            style={{ width: 188, marginBottom: 8, display: "block" }}
          />
          <Button
            type="primary"
            onClick={confirm}
            size="small"
            style={{ width: 90, marginRight: 8 }}
          >
            搜索
          </Button>
          <Button onClick={clearFilters} size="small" style={{ width: 90 }}>
            重置
          </Button>
        </div>
      ),
      onFilter: (value: string, record: KBFile) =>
        record.name.toLowerCase().includes(value.toLowerCase()),
      render: (text: string, file: KBFile) => (
        <Button
          type="link"
          onClick={() =>
            navigate("/data/knowledge-base/file-detail/" + file.id)
          }
        >
          {file.name}
        </Button>
      ),
    },
    {
      title: "类型",
      dataIndex: "type",
      key: "type",
      filters: allFileTypes.map((type) => ({
        text: type,
        value: type,
      })),
      onFilter: (value: string, record: KBFile) => record.type === value,
    },
    {
      title: "大小",
      dataIndex: "size",
      key: "size",
      sorter: (a: KBFile, b: KBFile) => parseFloat(a.size) - parseFloat(b.size),
      sortOrder: fileSortOrder,
    },
    {
      title: "向量化状态",
      dataIndex: "vectorizationStatus",
      key: "vectorizationStatus",
      filters: allVectorizationStatuses
        .filter((opt) => opt.value !== null)
        .map((opt) => ({
          text: opt.label,
          value: opt.value,
        })),
      onFilter: (value: string, record: KBFile) =>
        record.vectorizationStatus === value,
      render: (_: any, file: KBFile) => (
        <div className="flex items-center gap-2">
          <Badge
            status={getStatusBadgeVariant(
              file.vectorizationStatus || "pending"
            )}
            text={getStatusLabel(file.vectorizationStatus || "pending")}
          />
          {file.vectorizationStatus === "processing" && (
            <div className="w-16">
              <Progress percent={file.progress} size="small" showInfo={false} />
            </div>
          )}
        </div>
      ),
    },
    {
      title: "来源",
      dataIndex: "source",
      key: "source",
      render: (_: any, file: KBFile) => (
        <div className="flex items-center gap-2">
          <Badge
            status={file.source === "upload" ? "processing" : "default"}
            text={file.source === "upload" ? "上传" : "数据集"}
          />
          {file.datasetId && (
            <span className="text-xs text-gray-500">({file.datasetId})</span>
          )}
        </div>
      ),
    },
    {
      title: "分块数",
      dataIndex: "chunkCount",
      key: "chunkCount",
      render: (chunkCount: number) => (
        <span className="font-medium text-gray-900">{chunkCount}</span>
      ),
    },
    {
      title: "上传时间",
      dataIndex: "uploadedAt",
      key: "uploadedAt",
    },
    {
      title: "操作",
      key: "actions",
      align: "right" as const,
      render: (_: any, file: KBFile) => (
        <Dropdown
          menu={{
            items: [
              {
                label: "重试",
                key: "retry",
                onClick: () => handleStartVectorization(file.id),
              },
              {
                label: "删除",
                key: "delete",
                onClick: () => handleDeleteFile(file),
              },
            ],
          }}
        >
          <MoreHorizontal />
        </Dropdown>
      ),
    },
  ];

  return (
    <div className="">
      {/* Breadcrumb */}
      <div className="mb-4">
        <Breadcrumb>
          <Breadcrumb.Item>
            <a onClick={() => navigate("/data/knowledge-base")}>知识库</a>
          </Breadcrumb.Item>
          <Breadcrumb.Item>{knowledgeBase.name}</Breadcrumb.Item>
        </Breadcrumb>
      </div>
      <div className="flex flex-col gap-4">
        {/* Knowledge Base Header */}
        <DetailHeader
          data={{
            icon:
              knowledgeBase.type === "structured" ? (
                <Database className="w-8 h-8" />
              ) : (
                <BookOpen className="w-8 h-8" />
              ),
            status: {
              label: getStatusLabel(knowledgeBase.status),
              icon: getStatusIcon(knowledgeBase.status),
              color: getStatusBadgeVariant(knowledgeBase.status),
            },
            name: knowledgeBase.name,
            description: knowledgeBase.description,
            createdAt: knowledgeBase.createdAt,
            lastUpdated: knowledgeBase.lastUpdated,
          }}
          statistics={[
            {
              icon: <File className="w-4 h-4 text-gray-400" />,
              label: "文件",
              value: knowledgeBase.fileCount,
            },
            {
              icon: <Layers className="w-4 h-4 text-gray-400" />,
              label: "分块",
              value: knowledgeBase.chunkCount?.toLocaleString?.() ?? 0,
            },
            {
              icon: <StarOff className="w-4 h-4 text-gray-400" />,
              label: "向量",
              value: knowledgeBase.vectorCount?.toLocaleString?.() ?? 0,
            },
            {
              icon: <Database className="w-4 h-4 text-gray-400" />,
              label: "大小",
              value: knowledgeBase.size,
            },
          ]}
          operations={[
            {
              key: "edit",
              label: "修改参数配置",
              icon: <Edit className="w-4 h-4" />,
              onClick: () => {
                setEditForm(knowledgeBase);
                setCurrentView("config");
              },
            },
            {
              key: "vector",
              label: "向量化管理",
              icon: <VectorSquareIcon className="w-4 h-4" />,
              onClick: () => setShowVectorizationDialog(true),
            },
            ...(knowledgeBase.status === "error"
              ? [
                  {
                    key: "retry",
                    label: "重试",
                    onClick: () => {}, // 填写重试逻辑
                    danger: false,
                  },
                ]
              : []),
            {
              key: "more",
              label: "更多操作",
              icon: <MoreHorizontal className="w-4 h-4" />,
              isDropdown: true,
              items: [
                {
                  key: "download",
                  label: "导出",
                },
                {
                  key: "settings",
                  label: "配置",
                },
                { type: "divider" },
                {
                  key: "delete",
                  label: "删除",
                  danger: true,
                  onClick: () => handleDeleteKB(knowledgeBase),
                },
              ],
            },
          ]}
        />
        {/* Tab Navigation */}
        <Card>
          {/* Files Section */}
          <div className="flex items-center justify-between mb-4 gap-4">
            <div className="flex-1">
              <SearchControls
                searchTerm={fileSearchQuery}
                onSearchChange={setFileSearchQuery}
                searchPlaceholder="搜索文件名..."
                filters={[
                  {
                    key: "status",
                    label: "状态筛选",
                    options: [
                      { label: "全部状态", value: "all" },
                      { label: "已完成", value: "completed" },
                      { label: "处理中", value: "processing" },
                      { label: "向量化中", value: "vectorizing" },
                      { label: "错误", value: "error" },
                      { label: "已禁用", value: "disabled" },
                    ],
                  },
                ]}
                onFiltersChange={(filters) => {
                  setFileStatusFilter(filters.status?.[0] || "all");
                }}
                showViewToggle={false}
              />
            </div>
            <Button type="primary">
              <Plus className="w-4 h-4 mr-1" />
              添加文件
            </Button>
          </div>

          {/* Files Table */}
          <Table
            columns={fileColumns}
            dataSource={files}
            rowKey="id"
            pagination={false}
            locale={{
              emptyText: (
                <div className="text-center py-12">
                  <File className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    没有找到文件
                  </h3>
                  <p className="text-gray-500 mb-4">
                    尝试调整搜索条件或添加新文件
                  </p>
                  <Button type="dashed">
                    <Upload className="w-4 h-4 mr-2" />
                    添加文件
                  </Button>
                </div>
              ),
            }}
          />
        </Card>
      </div>
      {/* Vectorization Dialog */}
      <Modal
        open={showVectorizationDialog}
        onCancel={() => setShowVectorizationDialog(false)}
        footer={null}
        title="向量化管理"
        width={700}
        destroyOnClose
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Card className="p-4">
              <h4 className="font-medium mb-2">当前状态</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>已向量化文件:</span>
                  <span>
                    {
                      knowledgeBase.files.filter(
                        (f) => f.vectorizationStatus === "completed"
                      ).length
                    }
                    /{knowledgeBase.files.length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>向量总数:</span>
                  <span>
                    {knowledgeBase.vectorCount?.toLocaleString?.() ?? 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>存储大小:</span>
                  <span>{knowledgeBase.size}</span>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <h4 className="font-medium mb-2">操作选项</h4>
              <div className="space-y-2">
                <Button
                  className="w-full"
                  type="primary"
                  onClick={() => handleStartVectorization()}
                >
                  <Zap className="w-4 h-4 mr-2" />
                  批量向量化
                </Button>
                <Button
                  className="w-full"
                  onClick={() => message.info("TODO: 重新向量化全部")}
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  重新向量化全部
                </Button>
                <Button
                  className="w-full"
                  danger
                  onClick={() => message.info("TODO: 清空向量数据")}
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
              {knowledgeBase.files.map((file: KBFile) => (
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
                      status={getStatusBadgeVariant(
                        file.vectorizationStatus || "pending"
                      )}
                      text={getStatusLabel(
                        file.vectorizationStatus || "pending"
                      )}
                    />
                    {file.vectorizationStatus === "processing" && (
                      <div className="w-16">
                        <Progress
                          percent={file.progress}
                          size="small"
                          showInfo={false}
                        />
                      </div>
                    )}
                    {file.vectorizationStatus !== "completed" && (
                      <Button
                        size="small"
                        onClick={() => handleStartVectorization(file.id)}
                      >
                        <StarOff className="w-3 h-3" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="flex justify-end pt-2">
            <Button onClick={() => setShowVectorizationDialog(false)}>
              关闭
            </Button>
          </div>
        </div>
      </Modal>
      {/* Edit File Dialog */}
      <Modal
        open={!!showEditFileDialog}
        onCancel={() => setShowEditFileDialog(null)}
        title="编辑文件"
        width={600}
        footer={[
          <Button key="cancel" onClick={() => setShowEditFileDialog(null)}>
            取消
          </Button>,
          <Button
            key="save"
            type="primary"
            onClick={() => setShowEditFileDialog(null)}
          >
            <Save className="w-4 h-4 mr-2" />
            保存更改
          </Button>,
        ]}
        destroyOnClose
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block mb-1">文件名</label>
              <Input value={showEditFileDialog?.name} readOnly />
            </div>
            <div>
              <label className="block mb-1">文件来源</label>
              <Input
                value={
                  showEditFileDialog?.source === "upload"
                    ? "上传文件"
                    : "数据集文件"
                }
                readOnly
              />
            </div>
          </div>

          {showEditFileDialog?.source === "upload" ? (
            <div className="space-y-3">
              <label className="block mb-1">更新文件</label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm text-gray-600">
                  拖拽或点击上传新版本文件
                </p>
                <Button className="mt-2 bg-transparent" disabled>
                  选择文件
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <label className="block mb-1">数据集文件管理</label>
              <div className="p-4 border rounded-lg bg-gray-50">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">
                    当前数据集: {showEditFileDialog?.datasetId}
                  </span>
                  <Button size="small">
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
            <label className="block mb-1">处理选项</label>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Checkbox id="reprocess" />
                <span className="text-sm">更新后重新处理分块</span>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox id="revectorize" />
                <span className="text-sm">重新生成向量</span>
              </div>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default KnowledgeBaseDetailPage;
