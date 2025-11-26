import {DeleteOutlined, EditOutlined} from "@ant-design/icons";
import CardView from "@/components/CardView";
import {
  deleteCleaningTemplateByIdUsingDelete, queryCleaningTemplatesUsingGet,
} from "../../cleansing.api";
import useFetchData from "@/hooks/useFetchData";
import {mapTemplate} from "../../cleansing.const";
import {App, Button, Card, Table, Tooltip} from "antd";
import {CleansingTemplate} from "../../cleansing.model";
import {SearchControls} from "@/components/SearchControls.tsx";
import {useNavigate} from "react-router";
import {useState} from "react";

export default function TemplateList() {
  const navigate = useNavigate();
  const { message } = App.useApp();
  const [viewMode, setViewMode] = useState<"card" | "list">("list");

  const {
    loading,
    tableData,
    pagination,
    searchParams,
    setSearchParams,
    fetchData,
    handleFiltersChange,
  } = useFetchData(queryCleaningTemplatesUsingGet, mapTemplate);

  const templateOperations = () => {
    return [
      {
        key: "update",
        label: "编辑",
        icon: <EditOutlined />,
        onClick: (template: CleansingTemplate) => navigate(`/data/cleansing/update-template/${template.id}`)
      },
      {
        key: "delete",
        label: "删除",
        danger: true,
        icon: <DeleteOutlined />,
        onClick: deleteTemplate, // implement delete logic
      },
    ];
  };

  const templateColumns = [
    {
      title: "模板ID",
      dataIndex: "id",
      key: "id",
      fixed: "left",
      width: 100,
    },
    {
      title: "模板名称",
      dataIndex: "name",
      key: "name",
      fixed: "left",
      width: 150,
      ellipsis: true,
      render: (_, template: CleansingTemplate) => {
        return (
          <Button
            type="link"
            onClick={() =>
              navigate("/data/cleansing/template-detail/" + template.id)
            }
          >
            {template.name}
          </Button>
        );
      }},
      {
        title: "算子数量",
        dataIndex: "num",
        key: "num",
        width: 100,
        ellipsis: true,
        render: (_, template: CleansingTemplate) => {
          return template.instance?.length ?? 0;
        },
      },
      {
        title: "操作",
        key: "action",
        fixed: "right",
        width: 20,
        render: (text: string, record: any) => (
          <div className="flex gap-2">
            {templateOperations(record).map((op) =>
              op ? (
                <Tooltip key={op.key} title={op.label}>
                  <Button
                    type="text"
                    icon={op.icon}
                    danger={op?.danger}
                    onClick={() => op.onClick(record)}
                  />
                </Tooltip>
              ) : null
            )}
          </div>
        ),
      },
    ]

  const deleteTemplate = async (template: CleansingTemplate) => {
    if (!template.id) {
      return;
    }
    // 实现删除逻辑
    await deleteCleaningTemplateByIdUsingDelete(template.id);
    fetchData();
    message.success("模板删除成功");
  };

  return (
    <>
      {/* Search and Filters */}
      <SearchControls
        searchTerm={searchParams.keyword}
        onSearchChange={(keyword) =>
          setSearchParams({ ...searchParams, keyword })
        }
        searchPlaceholder="搜索模板名称、描述"
        onFiltersChange={handleFiltersChange}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        showViewToggle={true}
        onReload={fetchData}
        onClearFilters={() => setSearchParams({ ...searchParams, filter: {} })}
      />
      {viewMode === "card" ? (
        <CardView
          data={tableData}
          operations={templateOperations}
          pagination={pagination}
          onView={(tableData) => {
            navigate("/data/cleansing/template-detail/" + tableData.id)
          }}
        />
      ) : (
        <Card>
          <Table
            columns={templateColumns}
            dataSource={tableData}
            rowKey="id"
            loading={loading}
            scroll={{ x: "max-content", y: "calc(100vh - 35rem)" }}
            pagination={pagination}
          />
        </Card>
      )}
    </>
  );
}
