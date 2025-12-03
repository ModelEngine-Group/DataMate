import { useState } from "react";
import {
  Button,
  Card,
  Table,
  Tag,
  Space,
  Typography,
  Progress,
  Popconfirm,
  App,
} from "antd";
import {
  PlusOutlined,
  DeleteOutlined
} from "@ant-design/icons";
import { SearchControls } from "@/components/SearchControls";
import { useNavigate } from "react-router";
import { deleteEvaluationTaskUsingGet, getPagedEvaluationTaskUsingGet } from "@/pages/DataEvaluation/evaluation.api";
import CardView from "@/components/CardView";
import CreateTaskModal from "@/pages/DataEvaluation/Create/CreateTask.tsx";
import useFetchData from "@/hooks/useFetchData.ts";
import { EvaluationTask } from "@/pages/DataEvaluation/evaluation.model.ts";
import { mapEvaluationTask } from "@/pages/DataEvaluation/evaluation.const.tsx";

const { Text, Title } = Typography;

const statusMap = {
  PENDING: { text: '等待中', color: 'warning'},
  RUNNING: { text: '运行中', color: 'processing'},
  COMPLETED: { text: '已完成', color: 'success'},
  STOPPED: { text: '已停止', color: 'default'},
  FAILED: { text: '失败', color: 'error'},
};

export default function DataEvaluationPage() {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<"card" | "list">("list");
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
    mapEvaluationTask,
    30000,
    true,
    [],
    0
  );

  const [isModalVisible, setIsModalVisible] = useState(false);

  const handleDeleteTask = async (task: EvaluationTask) => {
    try {
      // 调用删除接口
      await deleteEvaluationTaskUsingGet(task.id);
      message.success("任务删除成功");
      // 重新加载数据
      fetchData().then();
    } catch (error) {
      message.error("任务删除失败，请稍后重试");
    }
  };

  const filterOptions = [
    {
      key: 'status',
      label: '状态',
      options: Object.entries(statusMap).map(([value, { text }]) => ({
        value,
        label: text,
      })),
    },
    {
      key: 'taskType',
      label: '任务类型',
      options: [
        { value: 'QA', label: 'QA评估' },
      ],
    },
    {
      key: 'evalMethod',
      label: '评估方式',
      options: [
        { value: 'AUTO', label: '自动评估' },
        { value: 'MANUAL', label: '人工评估' },
      ],
    },
  ];

  const columns = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      render: (name, record) => (
        <Button
          type="link"
          onClick={() => navigate(`/data/evaluation/detail/${record.id}`)}
        >
          {name}
        </Button>
      ),
    },
    {
      title: '任务类型',
      dataIndex: 'taskType',
      key: 'taskType',
      render: (text: string) => (
        <Tag color={text === 'QA' ? 'blue' : 'default'}>
          {text === 'QA' ? 'QA评估' : text}
        </Tag>
      ),
    },
    {
      title: '评估方式',
      dataIndex: 'evalMethod',
      key: 'evalMethod',
      render: (text: string) => (
        <Tag color={text === 'AUTO' ? 'geekblue' : 'orange'}>
          {text === 'AUTO' ? '自动评估' : '人工评估'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: any) => {
        return (<Tag color={status.color}> {status.label} </Tag>);
      },
    },
    {
      title: '进度',
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
      title: "创建时间",
      dataIndex: "updatedAt",
      key: "updatedAt",
      width: 180,
    },
    {
      title: '操作',
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
      label: "删除",
      danger: true,
      confirm: {
        title: "确认删除该任务？",
        description: "删除后该任务将无法恢复，请谨慎操作。",
        okText: "删除",
        cancelText: "取消",
        okType: "danger",
      },
      icon: <DeleteOutlined />,
      onClick: handleDeleteTask,
    }
  ];

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <Title level={4} style={{ margin: 0 }}>数据评估</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setIsModalVisible(true)}
        >
          创建评估任务
        </Button>
      </div>
      <>
        {/* 搜索、筛选和视图控制 */}
        <SearchControls
          searchTerm={searchParams.keyword}
          onSearchChange={(keyword) =>
            setSearchParams({ ...searchParams, keyword })
          }
          searchPlaceholder="搜索任务名称..."
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
