import type React from "react";
import { useEffect, useState } from "react";
import { Table, Badge, Button, Breadcrumb, Tooltip, App } from "antd";
import {
  DeleteOutlined,
  EditOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import { useNavigate, useParams } from "react-router";
import DetailHeader from "@/components/DetailHeader";
import { SearchControls } from "@/components/SearchControls";
import { KBFile, KnowledgeBaseItem } from "../knowledge-base.model";
import { mapFileData, mapKnowledgeBase } from "../knowledge-base.const";
import {
  deleteKnowledgeBaseByIdUsingDelete,
  deleteKnowledgeBaseFileByIdUsingDelete,
  queryKnowledgeBaseByIdUsingGet,
  queryKnowledgeBaseFilesUsingGet,
} from "../knowledge-base.api";
import useFetchData from "@/hooks/useFetchData";
import AddDataDialog from "../components/AddDataDialog";
import CreateKnowledgeBase from "../components/CreateKnowledgeBase";

const KnowledgeBaseDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { message } = App.useApp();
  const { id } = useParams<{ id: string }>();
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBaseItem>(null);
  const [showEdit, setShowEdit] = useState(false);

  const fetchKnowledgeBaseDetails = async (id: string) => {
    const { data } = await queryKnowledgeBaseByIdUsingGet(id);
    setKnowledgeBase(mapKnowledgeBase(data));
  };

  useEffect(() => {
    if (id) {
      fetchKnowledgeBaseDetails(id);
    }
  }, [id]);

  const {
    loading,
    tableData: files,
    searchParams,
    pagination,
    fetchData: fetchFiles,
    setSearchParams,
    handleFiltersChange,
  } = useFetchData<KBFile>(
    (params) => id ? queryKnowledgeBaseFilesUsingGet(id, params) : Promise.resolve({ data: [] }),
    mapFileData
  );

  // File table logic
  const handleDeleteFile = async (file: KBFile) => {
    try {
      await deleteKnowledgeBaseFileByIdUsingDelete(knowledgeBase.id, {
        ids: [file.id]
      });
      message.success("文件已删除");
      fetchFiles();
    } catch (error) {
      message.error("文件删除失败");
    }
  };

  const handleDeleteKB = async (kb: KnowledgeBaseItem) => {
    await deleteKnowledgeBaseByIdUsingDelete(kb.id);
    message.success("知识库已删除");
    navigate("/data/knowledge-base");
  };

  const handleRefreshPage = () => {
    fetchKnowledgeBaseDetails(knowledgeBase.id);
    fetchFiles();
    setShowEdit(false);
  };

  const operations = [
    {
      key: "edit",
      label: "编辑知识库",
      icon: <EditOutlined className="w-4 h-4" />,
      onClick: () => {
        setShowEdit(true);
      },
    },
    {
      key: "refresh",
      label: "刷新知识库",
      icon: <ReloadOutlined className="w-4 h-4" />,
      onClick: () => {
        handleRefreshPage();
      },
    },
    {
      key: "delete",
      label: "删除知识库",
      danger: true,
      confirm: {
        title: "确认删除该知识库吗？",
        description: "删除后将无法恢复，请谨慎操作。",
        cancelText: "取消",
        okText: "删除",
        okType: "danger",
        onConfirm: () => handleDeleteKB(knowledgeBase),
      },
      icon: <DeleteOutlined className="w-4 h-4" />,
    },
  ];

  const fileOps = [
    {
      key: "delete",
      label: "删除文件",
      icon: <DeleteOutlined className="w-4 h-4" />,
      danger: true,
      onClick: handleDeleteFile,
    },
  ];

  const fileColumns = [
    {
      title: "文件名",
      dataIndex: "name",
      key: "name",
      width: 200,
      ellipsis: true,
      fixed: "left" as const,
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "vectorizationStatus",
      width: 120,
      render: (status: any) => (
        <Badge color={status?.color} text={status?.label} />
      ),
    },
    {
      title: "分块数",
      dataIndex: "chunkCount",
      key: "chunkCount",
      width: 100,
      ellipsis: true,
    },
    {
      title: "创建时间",
      dataIndex: "createdAt",
      key: "createdAt",
      ellipsis: true,
      width: 180,
    },
    {
      title: "更新时间",
      dataIndex: "updatedAt",
      key: "updatedAt",
      ellipsis: true,
      width: 180,
    },
    {
      title: "操作",
      key: "actions",
      align: "right" as const,
      width: 100,
      render: (_: any, file: KBFile) => (
        <div>
          {fileOps.map((op) => (
            <Tooltip key={op.key} title={op.label}>
              <Button
                type="text"
                icon={op.icon}
                danger={op?.danger}
                onClick={() => op.onClick(file)}
              />
            </Tooltip>
          ))}
        </div>
      ),
    },
  ];

  return (
    <div className="h-full flex flex-col">
      <div className="mb-4">
        <Breadcrumb>
          <Breadcrumb.Item>
            <a onClick={() => navigate("/data/knowledge-base")}>知识库</a>
          </Breadcrumb.Item>
          <Breadcrumb.Item>{knowledgeBase?.name}</Breadcrumb.Item>
        </Breadcrumb>
      </div>
      <DetailHeader
        data={knowledgeBase}
        statistics={knowledgeBase?.statistics || []}
        operations={operations}
      />
      <CreateKnowledgeBase
        showBtn={false}
        isEdit={showEdit}
        data={knowledgeBase}
        onUpdate={handleRefreshPage}
        onClose={() => setShowEdit(false)}
      />
      <div className="flex-1 border-card p-6 mt-4">
        <div className="flex items-center justify-between mb-4 gap-3">
          <div className="flex-1">
            <SearchControls
              searchTerm={searchParams.keyword}
              onSearchChange={(keyword) =>
                setSearchParams({ ...searchParams, keyword })
              }
              searchPlaceholder="搜索文件名..."
              filters={[]}
              onFiltersChange={handleFiltersChange}
              onClearFilters={() =>
                setSearchParams({ ...searchParams, filter: {} })
              }
              showViewToggle={false}
              showReload={false}
            />
          </div>
          <AddDataDialog knowledgeBase={knowledgeBase} onDataAdded={handleRefreshPage} />
        </div>

        <Table
          loading={loading}
          columns={fileColumns}
          dataSource={files}
          rowKey="id"
          pagination={pagination}
          scroll={{ y: "calc(100vh - 30rem)" }}
        />
      </div>
    </div>
  );
};

export default KnowledgeBaseDetailPage;