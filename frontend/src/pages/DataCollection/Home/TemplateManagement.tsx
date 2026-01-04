import { App, Card, Table, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import { SearchControls } from "@/components/SearchControls";
import useFetchData from "@/hooks/useFetchData";
import { queryDataXTemplatesUsingGet } from "../collection.apis";
import { formatDateTime } from "@/utils/unit";

type CollectionTemplate = {
  id: string;
  name: string;
  description?: string;
  sourceType: string;
  sourceName: string;
  targetType: string;
  targetName: string;
  builtIn?: boolean;
  createdAt?: string;
  updatedAt?: string;
};

export default function TemplateManagement() {
  const { message } = App.useApp();

  const filters = [
    {
      key: "builtIn",
      label: "模板类型",
      options: [
        { value: "all", label: "全部" },
        { value: "true", label: "内置" },
        { value: "false", label: "自定义" },
      ],
    },
  ];

  const {
    loading,
    tableData,
    pagination,
    searchParams,
    setSearchParams,
    fetchData,
    handleFiltersChange,
  } = useFetchData<CollectionTemplate>(
    (params) => {
      const { keyword, builtIn, ...rest } = params || {};
      const builtInValue = Array.isArray(builtIn)
        ? builtIn?.[0]
        : builtIn;

      return queryDataXTemplatesUsingGet({
        ...rest,
        name: keyword || undefined,
        built_in:
          builtInValue && builtInValue !== "all"
            ? builtInValue === "true"
            : undefined,
      });
    },
    (tpl) => ({
      ...tpl,
      createdAt: tpl.createdAt ? formatDateTime(tpl.createdAt) : "-",
      updatedAt: tpl.updatedAt ? formatDateTime(tpl.updatedAt) : "-",
    }),
    30000,
    false,
    [],
    0
  );

  const columns: ColumnsType<CollectionTemplate> = [
    {
      title: "模板名称",
      dataIndex: "name",
      key: "name",
      fixed: "left",
      width: 200,
      ellipsis: true,
    },
    {
      title: "模板类型",
      dataIndex: "builtIn",
      key: "builtIn",
      width: 120,
      render: (v?: boolean) => (
        <Tag color={v ? "blue" : "default"}>{v ? "内置" : "自定义"}</Tag>
      ),
    },
    {
      title: "源端",
      key: "source",
      width: 220,
      ellipsis: true,
      render: (_: any, record: CollectionTemplate) => (
        <span>{`${record.sourceType} / ${record.sourceName}`}</span>
      ),
    },
    {
      title: "目标端",
      key: "target",
      width: 220,
      ellipsis: true,
      render: (_: any, record: CollectionTemplate) => (
        <span>{`${record.targetType} / ${record.targetName}`}</span>
      ),
    },
    {
      title: "描述",
      dataIndex: "description",
      key: "description",
      width: 260,
      ellipsis: true,
      render: (v?: string) => v || "-",
    },
    {
      title: "创建时间",
      dataIndex: "createdAt",
      key: "createdAt",
      width: 160,
    },
    {
      title: "更新时间",
      dataIndex: "updatedAt",
      key: "updatedAt",
      width: 160,
    },
  ];

  return (
    <div className="space-y-4">
      <SearchControls
        searchTerm={searchParams.keyword}
        onSearchChange={(newSearchTerm) =>
          setSearchParams((prev) => ({
            ...prev,
            keyword: newSearchTerm,
            current: 1,
          }))
        }
        searchPlaceholder="搜索模板名称..."
        filters={filters}
        onFiltersChange={handleFiltersChange}
        showViewToggle={false}
        onClearFilters={() =>
          setSearchParams((prev) => ({
            ...prev,
            filter: { ...prev.filter, builtIn: [] },
            current: 1,
          }))
        }
        onReload={() => {
          fetchData().catch(() => message.error("刷新失败"));
        }}
      />

      <Card>
        <Table
          columns={columns}
          dataSource={tableData}
          loading={loading}
          rowKey="id"
          pagination={{
            ...pagination,
            current: searchParams.current,
            pageSize: searchParams.pageSize,
            total: pagination.total,
          }}
          scroll={{ x: "max-content", y: "calc(100vh - 25rem)" }}
        />
      </Card>
    </div>
  );
}
