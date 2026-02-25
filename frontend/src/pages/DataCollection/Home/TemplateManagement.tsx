import { App, Card, Table, Tag, Dropdown, Button } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { MenuProps } from "antd";
import { SearchControls } from "@/components/SearchControls";
import useFetchData from "@/hooks/useFetchData";
import { queryDataXTemplatesUsingGet } from "../collection.apis";
import { formatDateTime } from "@/utils/unit";
import { useTranslation } from "react-i18next";
import { SettingOutlined } from "@ant-design/icons";
import { useState, useMemo } from "react";

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

// 所有可用的列配置
const ALL_COLUMNS = {
  name: 'dataCollection.templateManagement.columns.templateName',
  builtIn: 'dataCollection.templateManagement.columns.templateType',
  source: 'dataCollection.templateManagement.columns.source',
  target: 'dataCollection.templateManagement.columns.target',
  description: 'dataCollection.templateManagement.columns.description',
  createdAt: 'dataCollection.templateManagement.columns.createdAt',
  updatedAt: 'dataCollection.templateManagement.columns.updatedAt',
} as const;

// 默认隐藏的列
const DEFAULT_HIDDEN_COLUMNS = ['createdAt', 'updatedAt'];

export default function TemplateManagement() {
  const { message } = App.useApp();
  const { t } = useTranslation();
  const [hiddenColumns, setHiddenColumns] = useState<Set<string>>(new Set(DEFAULT_HIDDEN_COLUMNS));

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
      const { keyword, ...rest } = params || {};
      return queryDataXTemplatesUsingGet({
        ...rest,
        name: keyword || undefined,
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

  // 根据隐藏列的状态动态生成 columns
  const columns: ColumnsType<CollectionTemplate> = useMemo(() => {
    const allColumns: ColumnsType<CollectionTemplate> = [
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
        render: (_: any, record: CollectionTemplate) => {
          // 如果 sourceType 和 sourceName 相同，只显示一个
          if (record.sourceType === record.sourceName) {
            return <span>{record.sourceType}</span>;
          }
          return <span>{`${record.sourceType} / ${record.sourceName}`}</span>;
        },
      },
      {
        title: t("dataCollection.templateManagement.columns.target"),
        key: "target",
        width: 220,
        ellipsis: true,
        render: (_: any, record: CollectionTemplate) => {
          // 如果 targetType 和 targetName 相同，只显示一个
          if (record.targetType === record.targetName) {
            return <span>{record.targetType}</span>;
          }
          return <span>{`${record.targetType} / ${record.targetName}`}</span>;
        },
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

    // 过滤掉隐藏的列
    return allColumns.filter(col => !hiddenColumns.has(col.key as string));
  }, [t, hiddenColumns]);

  // 列显示切换处理
  const handleColumnToggle = (columnKey: string) => {
    setHiddenColumns(prev => {
      const newHidden = new Set(prev);
      if (newHidden.has(columnKey)) {
        newHidden.delete(columnKey);
      } else {
        newHidden.add(columnKey);
      }
      return newHidden;
    });
  };

  // 列选择菜单
  const columnMenuItems: MenuProps['items'] = Object.entries(ALL_COLUMNS).map(([key, label]) => ({
    key,
    label: t(label),
  }));

  // 获取显示的列（非隐藏列）
  const visibleColumns = Object.keys(ALL_COLUMNS).filter(key => !hiddenColumns.has(key));

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
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
          selectedFilters={searchParams.filter}
          onFiltersChange={handleFiltersChange}
          showViewToggle={false}
          showReload={true}
          onClearFilters={() =>
            setSearchParams((prev) => ({
              ...prev,
              filter: { ...prev.filter, builtIn: [] },
              current: 1,
              keyword: "",
            }))
          }
          onReload={() => {
            fetchData().catch(() => message.error(t("dataCollection.templateManagement.messages.refreshFailed")));
          }}
          className="flex-1"
        />
        <Dropdown
          menu={{
            items: columnMenuItems,
            selectable: true,
            multiple: true,
            selectedKeys: visibleColumns,
            onClick: ({ key }) => handleColumnToggle(key as string),
          }}
        >
          <Button icon={<SettingOutlined />}>
            {t("dataCollection.templateManagement.columnSettings")}
          </Button>
        </Dropdown>
      </div>

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
