import { useState } from "react";
import { Card, Button, Table, Tooltip, message } from "antd";
import { DeleteOutlined, EditOutlined } from "@ant-design/icons";
import { SearchControls } from "@/components/SearchControls";
import { useNavigate } from "react-router";
import CardView from "@/components/CardView";
import {
  deleteKnowledgeBaseByIdUsingDelete,
  queryKnowledgeBasesUsingPost,
} from "../knowledge-base.api";
import useFetchData from "@/hooks/useFetchData";
import { KnowledgeBaseItem } from "../knowledge-base.model";
import CreateKnowledgeBase from "../components/CreateKnowledgeBase";
import { mapKnowledgeBase } from "../knowledge-base.const";

export default function KnowledgeBasePage() {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<"card" | "list">("card");
  const [isEdit, setIsEdit] = useState(false);
  const [currentKB, setCurrentKB] = useState<KnowledgeBaseItem | null>(null);
  const {
    loading,
    tableData,
    searchParams,
    pagination,
    fetchData,
    setSearchParams,
    handleFiltersChange,
  } = useFetchData<KnowledgeBaseItem>(
    queryKnowledgeBasesUsingPost,
    mapKnowledgeBase
  );

  const handleDeleteKB = async (kb: KnowledgeBaseItem) => {
    try {
      await deleteKnowledgeBaseByIdUsingDelete(kb.id);
      message.success("知识库删除成功");
      fetchData();
    } catch (error) {
      message.error("知识库删除失败");
    }
  };

  const operations = [
    {
      key: "edit",
      label: "编辑",
      icon: <EditOutlined />,
      onClick: (item) => {
        setIsEdit(true);
        setCurrentKB(item);
      },
    },
    {
      key: "delete",
      label: "删除",
      danger: true,
      icon: <DeleteOutlined />,
      confirm: {
        title: "确认删除",
        description: "此操作不可撤销，是否继续？",
        okText: "删除",
        okType: "danger",
        cancelText: "取消",
      },
      onClick: (item) => handleDeleteKB(item),
    },
  ];

  const columns = [
    {
      title: "知识库",
      dataIndex: "name",
      key: "name",
      fixed: "left" as const,
      width: 200,
      ellipsis: true,
      render: (_: any, kb: KnowledgeBaseItem) => (
        <Button
          type="link"
          onClick={() => navigate(`/data/knowledge-base/detail/${kb.id}`)}
        >
          {kb.name}
        </Button>
      ),
    },
    {
      title: "向量数据库",
      dataIndex: "embeddingModel",
      key: "embeddingModel",
      width: 150,
      ellipsis: true,
    },
    {
      title: "大语言模型",
      dataIndex: "chatModel",
      key: "chatModel",
      width: 150,
      ellipsis: true,
    },
    {
      title: "创建时间",
      dataIndex: "createdAt",
      key: "createdAt",
      ellipsis: true,
      width: 150,
    },
    {
      title: "更新时间",
      dataIndex: "updatedAt",
      key: "updatedAt",
      ellipsis: true,
      width: 150,
    },
    {
      title: "描述",
      dataIndex: "description",
      key: "description",
      width: 120,
      ellipsis: true,
    },
    {
      title: "操作",
      key: "actions",
      fixed: "right" as const,
      width: 150,
      render: (_: any, kb: KnowledgeBaseItem) => (
        <div className="flex items-center gap-2">
          {operations.map((op) => (
            <Tooltip key={op.key} title={op.label}>
              <Button
                type="text"
                icon={op.icon}
                danger={op.danger}
                onClick={() => op.onClick(kb)}
              />
            </Tooltip>
          ))}
        </div>
      ),
    },
  ];
  // Main list view
  return (
    <div className="h-full flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">知识生成</h1>
        <CreateKnowledgeBase
          isEdit={isEdit}
          data={currentKB}
          onUpdate={() => {
            fetchData();
          }}
          onClose={() => {
            setIsEdit(false);
            setCurrentKB(null);
          }}
        />
      </div>

      <SearchControls
        searchTerm={searchParams.keyword}
        onSearchChange={(keyword) =>
          setSearchParams({ ...searchParams, keyword })
        }
        searchPlaceholder="搜索知识库..."
        filters={[]}
        onFiltersChange={handleFiltersChange}
        onClearFilters={() => setSearchParams({ ...searchParams, filter: {} })}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        showViewToggle
        onReload={fetchData}
      />
      {viewMode === "card" ? (
        <CardView
          data={tableData}
          operations={operations}
          onView={(item) => navigate(`/data/knowledge-base/detail/${item.id}`)}
          pagination={pagination}
        />
      ) : (
        <Card>
          <Table
            loading={loading}
            scroll={{ x: "max-content", y: "calc(100vh - 20rem)" }}
            columns={columns}
            dataSource={tableData}
            rowKey="id"
          />
        </Card>
      )}
    </div>
  );
}
