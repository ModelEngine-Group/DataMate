import { App, Card, Table, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import { SearchControls } from "@/components/SearchControls";
import useFetchData from "@/hooks/useFetchData";
import { queryDataXTemplatesUsingGet } from "../collection.apis";
import { formatDateTime } from "@/utils/unit";
import { useTranslation } from "react-i18next";

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
  const { t } = useTranslation();

  const filters = [
    {
      key: "builtIn",
      label: t("dataCollection.templateManagement.filters.templateType"),
      options: [
        { value: "all", label: t("dataCollection.templateManagement.filters.all") },
        { value: "true", label: t("dataCollection.templateManagement.filters.builtIn") },
        { value: "false", label: t("dataCollection.templateManagement.filters.custom") },
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
      title: t("dataCollection.templateManagement.columns.templateName"),
      dataIndex: "name",
      key: "name",
      fixed: "left",
      width: 200,
      ellipsis: true,
    },
    {
      title: t("dataCollection.templateManagement.columns.templateType"),
      dataIndex: "builtIn",
      key: "builtIn",
      width: 120,
      render: (v?: boolean) => (
        <Tag color={v ? "blue" : "default"}>
          {v
            ? t("dataCollection.templateManagement.filters.builtIn")
            : t("dataCollection.templateManagement.filters.custom")}
        </Tag>
      ),
    },
    {
      title: t("dataCollection.templateManagement.columns.source"),
      key: "source",
      width: 220,
      ellipsis: true,
      render: (_: any, record: CollectionTemplate) => (
        <span>{`${record.sourceType} / ${record.sourceName}`}</span>
      ),
    },
    {
      title: t("dataCollection.templateManagement.columns.target"),
      key: "target",
      width: 220,
      ellipsis: true,
      render: (_: any, record: CollectionTemplate) => (
        <span>{`${record.targetType} / ${record.targetName}`}</span>
      ),
    },
    {
      title: t("dataCollection.templateManagement.columns.description"),
      dataIndex: "description",
      key: "description",
      width: 260,
      ellipsis: true,
      render: (v?: string) => v || t("common.placeholders.empty"),
    },
    {
      title: t("dataCollection.templateManagement.columns.createdAt"),
      dataIndex: "createdAt",
      key: "createdAt",
      width: 160,
    },
    {
      title: t("dataCollection.templateManagement.columns.updatedAt"),
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
        searchPlaceholder={t("dataCollection.templateManagement.filters.searchPlaceholder")}
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
          fetchData().catch(() => message.error(t("dataCollection.templateManagement.messages.refreshFailed")));
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
