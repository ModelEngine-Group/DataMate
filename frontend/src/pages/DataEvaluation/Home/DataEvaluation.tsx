import { useState, useEffect } from "react";
import {
  Button,
  Card,
  Table,
  Tag,
  Typography,
  Progress,
  Popconfirm,
  App,
} from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import { SearchControls } from "@/components/SearchControls";
import { useNavigate } from "react-router";
import { Plus } from "lucide-react";
import { deleteEvaluationTaskUsingGet, getPagedEvaluationTaskUsingGet } from "@/pages/DataEvaluation/evaluation.api";
import CardView from "@/components/CardView";
import CreateTaskModal from "@/pages/DataEvaluation/Create/CreateTask.tsx";
import useFetchData from "@/hooks/useFetchData.ts";
import { EvaluationTask } from "@/pages/DataEvaluation/evaluation.model.ts";
import {
  getEvalTaskStatusMap,
  getEvalMethods,
  getTaskTypes,
  mapEvaluationTask,
} from "@/pages/DataEvaluation/evaluation.const.tsx";
import { useTranslation } from "react-i18next";

const { Text, Title } = Typography;

export default function DataEvaluationPage() {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [viewMode, setViewMode] = useState<"card" | "list">("list");

  const statusMap = getEvalTaskStatusMap(t);
  const taskTypes = getTaskTypes(t);
  const evalMethods = getEvalMethods(t);

  const {
    loading,
    tableData,
    pagination,
    searchParams,
    setSearchParams,
    handleFiltersChange,
    fetchData,
  } = useFetchData<EvaluationTask>(
    getPagedEvaluationTaskUsingGet,
    (item) => mapEvaluationTask(item, t),
    30000,
    true,
    [],
    0
  );

  useEffect(() => {
    fetchData();
  }, [t]);

  const [isModalVisible, setIsModalVisible] = useState(false);

  const handleDeleteTask = async (task: EvaluationTask) => {
    try {
      // 调用删除接口
      await deleteEvaluationTaskUsingGet(task.id);
      message.success(t("dataEvaluation.home.messages.deleteSuccess"));
      // 重新加载数据
      fetchData().then();
    } catch (error) {
      message.error(t("dataEvaluation.home.messages.deleteFailed"));
    }
  };

  const filterOptions = [
    {
      key: 'status',
      label: t("dataEvaluation.home.filters.status"),
      options: Object.entries(statusMap).map(([value, { label }]) => ({
        value,
        label,
      })),
    },
    {
      key: 'taskType',
      label: t("dataEvaluation.home.filters.taskType"),
      options: taskTypes,
    },
    {
      key: 'evalMethod',
      label: t("dataEvaluation.home.filters.evalMethod"),
      options: evalMethods,
    },
  ];

  const columns = [
    {
      title: t("dataEvaluation.home.columns.taskName"),
      dataIndex: 'name',
      key: 'name',
      fixed: "left" as const,
      render: (name, record) => (
        <a
          type="link"
          onClick={() => navigate(`/data/evaluation/detail/${record.id}`)}
        >
          {name}
        </a>
      ),
    },
    {
      title: t("dataEvaluation.home.columns.taskType"),
      dataIndex: 'taskType',
      key: 'taskType',
      render: (text: string) => (
        <Tag color={text === 'QA' ? 'blue' : 'default'}>
          {text === 'QA' ? t("dataEvaluation.create.taskTypes.qa") : t("dataEvaluation.create.taskTypes.cot")}
        </Tag>
      ),
    },
    {
      title: t("dataEvaluation.home.columns.evalMethod"),
      dataIndex: 'evalMethod',
      key: 'evalMethod',
      render: (text: string) => (
        <Tag color={text === 'AUTO' ? 'geekblue' : 'orange'}>
          {text === 'AUTO'
            ? t("dataEvaluation.create.evalMethods.auto")
            : t("dataEvaluation.create.evalMethods.manual")}
        </Tag>
      ),
    },
    {
      title: t("dataEvaluation.home.columns.status"),
      dataIndex: 'status',
      key: 'status',
      render: (status: any) => {
        return (<Tag color={status.color}> {status.label} </Tag>);
      },
    },
    {
      title: t("dataEvaluation.home.columns.progress"),
      dataIndex: 'evalProcess',
      key: 'evalProcess',
      render: (progress: number, record: EvaluationTask) => (
        <Progress
          percent={Math.round(progress * 100)}
          size="small"
          status={record.status === 'FAILED' ? 'exception' : 'active'}
        />
      ),
    },
    {
      title: t("dataEvaluation.home.columns.createdAt"),
      dataIndex: "updatedAt",
      key: "updatedAt",
      width: 180,
    },
    {
      title: t("dataEvaluation.home.columns.actions"),
      key: 'action',
      render: (_: any, task: EvaluationTask) => (
        <div className="flex items-center gap-2">
          {operations.map((op) => {
            if (op.confirm) {
              <Popconfirm
                title={op.confirm.title}
                description={op.confirm.description}
                onConfirm={() => op.onClick(task)}
              >
                <Button type="text" icon={op.icon} />
              </Popconfirm>;
            }
            return (
              <Button
                key={op.key}
                type="text"
                icon={op.icon}
                danger={op.danger}
                onClick={() => op.onClick(task)}
              />
            );
          })}
        </div>
      ),
    },
  ];

  const operations = [
    {
      key: "delete",
      label: t("dataEvaluation.home.confirm.okText"),
      danger: true,
      confirm: {
        title: t("dataEvaluation.home.confirm.deleteTitle"),
        description: t("dataEvaluation.home.confirm.deleteDesc"),
        okText: t("dataEvaluation.home.confirm.okText"),
        cancelText: t("dataEvaluation.home.confirm.cancelText"),
        okType: "danger",
      },
      icon: <DeleteOutlined />,
      onClick: handleDeleteTask,
    }
  ];

  return (
    <div className="h-full flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">{t("dataEvaluation.home.title")}</h2>
        <Button
          type="primary"
          icon={<Plus className="w-4 h-4" />}
          onClick={() => setIsModalVisible(true)}
        >
          {t("dataEvaluation.home.createTask")}
        </Button>
      </div>
      <>
        {/* 搜索、筛选和视图控制 */}
        <SearchControls
          searchTerm={searchParams.keyword}
          onSearchChange={(keyword) =>
            setSearchParams({ ...searchParams, keyword })
          }
          searchPlaceholder={t("dataEvaluation.home.searchPlaceholder")}
          filters={filterOptions}
          onFiltersChange={handleFiltersChange}
          onClearFilters={() =>
            setSearchParams({ ...searchParams, filter: {} })
          }
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          showViewToggle
          onReload={fetchData}
        />
        {/* 任务列表 */}
        {viewMode === "list" ? (
          <Card>
            <Table
              columns={columns}
              dataSource={tableData}
              pagination={pagination}
              rowKey="id"
              scroll={{ x: "max-content", y: "calc(100vh - 30rem)" }}
            />
          </Card>
        ) : (
          <CardView
            loading={loading}
            data={tableData}
            operations={operations}
            pagination={pagination}
            onView={(task) => {
              navigate(`/data/evaluation/detail/${task.id}`);
            }}
          />
        )}
      </>
      <CreateTaskModal
        visible={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        onSuccess={() => {
          setIsModalVisible(false);
          fetchData();
        }}
      />
    </div>
  );
}
