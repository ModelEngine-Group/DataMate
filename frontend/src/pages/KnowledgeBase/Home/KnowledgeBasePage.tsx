import { useState, useEffect } from "react";
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
import { useTranslation } from "react-i18next";

export default function KnowledgeBasePage() {
  const { t } = useTranslation();
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
    handleKeywordChange,
  } = useFetchData<KnowledgeBaseItem>(
    queryKnowledgeBasesUsingPost,
    (kb) => mapKnowledgeBase(kb, false, t) // 在首页不显示索引模型和文本理解模型字段
  );

  useEffect(() => {
    fetchData();
  }, [t])

  const handleDeleteKB = async (kb: KnowledgeBaseItem) => {
    try {
      await deleteKnowledgeBaseByIdUsingDelete(kb.id);
      message.success(t("knowledgeBase.home.messages.deleteSuccess"));
      fetchData();
    } catch (error) {
      message.error(t("knowledgeBase.home.messages.deleteFailed"));
    }
  };

  const operations = [
    {
      key: "edit",
      label: t("knowledgeBase.home.actions.edit"),
      icon: <EditOutlined />,
      onClick: (item) => {
        setIsEdit(true);
        setCurrentKB(item);
      },
    },
    {
      key: "delete",
      label: t("knowledgeBase.home.actions.delete"),
      danger: true,
      icon: <DeleteOutlined />,
      confirm: {
        title: t("knowledgeBase.home.confirm.deleteTitle"),
        description: t("knowledgeBase.home.confirm.deleteDescription"),
        okText: t("knowledgeBase.home.confirm.okText"),
        okType: "danger" as const,
        cancelText: t("knowledgeBase.home.confirm.cancelText"),
      },
      onClick: (item) => handleDeleteKB(item),
    },
  ];

  const columns = [
    {
      title: t("knowledgeBase.home.columns.name"),
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
      title: t("knowledgeBase.home.columns.createdAt"),
      dataIndex: "createdAt",
      key: "createdAt",
      ellipsis: true,
      width: 150,
    },
    {
      title: t("knowledgeBase.home.columns.updatedAt"),
      dataIndex: "updatedAt",
      key: "updatedAt",
      ellipsis: true,
      width: 150,
    },
    {
      title: t("knowledgeBase.home.columns.description"),
      dataIndex: "description",
      key: "description",
      width: 120,
      ellipsis: true,
    },
    {
      title: t("knowledgeBase.home.columns.actions"),
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
        <h1 className="text-xl font-bold">{t("knowledgeBase.title")}</h1>
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
        onSearchChange={handleKeywordChange}
        searchPlaceholder={t("knowledgeBase.home.searchPlaceholder")}
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
