import { useState, useEffect } from "react";
import { Card, Button, Table, Modal, message, Tooltip, Form, Input, Select } from "antd";
import {
  Plus,
  ArrowUp,
  ArrowDown,
  Sparkles,
} from "lucide-react";
import { FolderOpenOutlined, DeleteOutlined, EyeOutlined, ExperimentOutlined } from "@ant-design/icons";
import { Link, useNavigate } from "react-router";
import { SearchControls } from "@/components/SearchControls";
import { formatDateTime } from "@/utils/unit";
import {
  querySynthesisTasksUsingGet,
  deleteSynthesisTaskByIdUsingDelete,
  archiveSynthesisTaskToDatasetUsingPost,
} from "@/pages/SynthesisTask/synthesis-api";
import { createDatasetUsingPost } from "@/pages/DataManagement/dataset.api";
import { createEvaluationTaskUsingPost } from "@/pages/DataEvaluation/evaluation.api";
import { queryModelListUsingGet } from "@/pages/SettingsPage/settings.apis";
import { ModelI } from "@/pages/SettingsPage/ModelAccess";

interface SynthesisTask {
  id: string;
  name: string;
  description?: string;
  status: string;
  synthesis_type: string;
  model_id: string;
  progress?: number;
  result_data_location?: string;
  text_split_config?: {
    chunk_size: number;
    chunk_overlap: number;
  };
  synthesis_config?: {
    temperature?: number | null;
    prompt_template?: string;
    synthesis_count?: number | null;
  };
  source_file_id?: string[];
  total_files?: number;
  processed_files?: number;
  total_chunks?: number;
  processed_chunks?: number;
  total_synthesis_data?: number;
  created_at: string;
  updated_at?: string;
  created_by?: string;
  updated_by?: string;
}

export default function SynthesisTaskTab() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [tasks, setTasks] = useState<SynthesisTask[]>([]);
  const [filterStatus, setFilterStatus] = useState("all");
  const [sortBy, setSortBy] = useState<"createdAt" | "name">("createdAt");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [evalModalVisible, setEvalModalVisible] = useState(false);
  const [currentEvalTask, setCurrentEvalTask] = useState<SynthesisTask | null>(null);
  const [evalLoading, setEvalLoading] = useState(false);
  const [models, setModels] = useState<ModelI[]>([]);
  const [modelLoading, setModelLoading] = useState(false);

  const [evalForm] = Form.useForm();

  // 获取任务列表
  const loadTasks = async () => {
    setLoading(true);
    try {
      const params = {
        page: page,
        page_size: pageSize,
      } as {
        page?: number;
        page_size?: number;
        synthesis_type?: string;
        status?: string;
        name?: string;
      };
      if (searchQuery) params.name = searchQuery;
      if (filterStatus !== "all") params.synthesis_type = filterStatus;
      const res = await querySynthesisTasksUsingGet(params);
      setTasks(res?.data?.content || []);
      setTotal(res?.data?.totalElements || 0);
    } catch {
      setTasks([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
    // eslint-disable-next-line
  }, [searchQuery, filterStatus, page, pageSize]);

  // 类型映射
  const typeMap: Record<string, string> = {
    QA: "问答对生成",
    COT: "链式推理生成",
  };

  // 表格列
  const ellipsisStyle = {
    maxWidth: 100,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    display: "inline-block",
    verticalAlign: "middle",
  };
  const taskColumns = [

    {
      title: (
        <Button
          type="text"
          onClick={() => {
            if (sortBy === "name") {
              setSortOrder(sortOrder === "asc" ? "desc" : "asc");
            } else {
              setSortBy("name");
              setSortOrder("desc");
            }
          }}
          className="h-auto p-0 font-semibold text-gray-700 hover:bg-transparent"
        >
          任务名称
          {sortBy === "name" &&
            (sortOrder === "asc" ? (
              <ArrowUp className="w-3 h-3 ml-1" />
            ) : (
              <ArrowDown className="w-3 h-3 ml-1" />
            ))}
        </Button>
      ),
      dataIndex: "name",
      key: "name",
      fixed: "left" as const,
      width: 160,
      render: (_: unknown, task: SynthesisTask) => (
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center shadow-sm">
            <span className="text-white font-bold text-base">
              {task.synthesis_type?.toUpperCase()?.slice(0, 1) || "T"}
            </span>
          </div>
          <Tooltip title={task.name} placement="top">
            <div style={{ ...ellipsisStyle, maxWidth: 100 }}>
              <Link to={`/data/synthesis/task/${task.id}`}>{task.name}</Link>
            </div>
          </Tooltip>
        </div>
      ),
    },
    {
      title: "任务ID",
      dataIndex: "id",
      key: "id",
      width: 140,
      render: (id: string) => (
        <Tooltip title={id} placement="top">
          <span style={{ ...ellipsisStyle, maxWidth: 140 }}>{id}</span>
        </Tooltip>
      ),
    },
    {
      title: "类型",
      dataIndex: "synthesis_type",
      key: "synthesis_type",
      width: 100,
      render: (type: string) => (
        <Tooltip title={typeMap[type] || type} placement="top">
          <span style={{ ...ellipsisStyle, maxWidth: 100 }}>{typeMap[type] || type}</span>
        </Tooltip>
      ),
    },
    {
      title: "文件数",
      dataIndex: "total_files",
      key: "total_files",
      width: 70,
      render: (num: number, task: SynthesisTask) => (
        <Tooltip title={num ?? (task.source_file_id?.length ?? 0)} placement="top">
          <span style={{ ...ellipsisStyle, maxWidth: 70 }}>{num ?? (task.source_file_id?.length ?? 0)}</span>
        </Tooltip>
      ),
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      key: "created_at",
      width: 200,
      render: (val: string) => (
        <Tooltip title={formatDateTime(val)} placement="top">
          <span style={{ ...ellipsisStyle, maxWidth: 200 }}>{formatDateTime(val)}</span>
        </Tooltip>
      ),
    },
    {
      title: "操作",
      key: "actions",
      fixed: "right" as const,
      width: 120,
      render: (_: unknown, task: SynthesisTask) => (
        <div className="flex items-center justify-start gap-1">
          <Tooltip title="查看详情">
            <Button
              onClick={() => navigate(`/data/synthesis/task/${task.id}`)}
              className="hover:bg-blue-50 p-1 h-7 w-7 flex items-center justify-center"
              type="text"
              icon={<EyeOutlined />}
            />
          </Tooltip>
          <Tooltip title="立即评估">
            <Button
              type="text"
              className="hover:bg-purple-50 p-1 h-7 w-7 flex items-center justify-center text-purple-600"
              icon={<ExperimentOutlined />}
              onClick={() => openEvalModal(task)}
            />
          </Tooltip>
          <Tooltip title="留用合成数据到数据集">
            <Button
              type="text"
              className="hover:bg-green-50 p-1 h-7 w-7 flex items-center justify-center text-green-600"
              icon={<FolderOpenOutlined />}
              onClick={() => {
                Modal.confirm({
                  title: "确认归档该合成任务?",
                  content: `任务名称：${task.name}`,
                  okText: "归档",
                  cancelText: "取消",
                  onOk: () => handleArchiveTask(task),
                });
              }}
            />
          </Tooltip>
          <Tooltip title="删除任务">
            <Button
              danger
              type="text"
              className="hover:bg-red-50 p-1 h-7 w-7 flex items-center justify-center"
              icon={<DeleteOutlined />}
              onClick={() => {
                Modal.confirm({
                  title: `确认删除任务?`,
                  content: `任务名：${task.name}`,
                  okText: "删除",
                  okType: "danger",
                  cancelText: "取消",
                  onOk: async () => {
                    try {
                      await deleteSynthesisTaskByIdUsingDelete(task.id);
                      message.success("删除成功");
                      loadTasks();
                    } catch {
                      message.error("删除失败");
                    }
                  },
                });
              }}
            />
          </Tooltip>
        </div>
      ),
    },
  ];

  const handleArchiveTask = async (task: SynthesisTask) => {
    try {
      // 1. 创建目标数据集（使用简单的默认命名 + 随机后缀，可后续扩展为弹窗自定义）
      const randomSuffix = Math.random().toString(36).slice(2, 8);
      const datasetReq: {
        name: string;
        description: string;
        datasetType: string;
        category: string;
        format: string;
        status: string;
      } = {
        name: `${task.name}-合成数据留用${randomSuffix}`,
        description: `由合成任务 ${task.id} 留用生成`,
        datasetType: "TEXT",
        category: "SYNTHESIS",
        format: "JSONL",
        status: "DRAFT",
      };
      const datasetRes = await createDatasetUsingPost(datasetReq);
      const datasetId = datasetRes?.data?.id;
      if (!datasetId) {
        message.error("创建数据集失败");
        return;
      }

      // 2. 调用后端归档接口，将合成数据写入该数据集
      await archiveSynthesisTaskToDatasetUsingPost(task.id, datasetId);

      message.success("归档成功");
      // 3. 可选：跳转到数据集详情页
      navigate(`/data/management/detail/${datasetId}`);
    } catch (e) {
      console.error(e);
      message.error("归档失败");
    }
  };

  const openEvalModal = (task: SynthesisTask) => {
    setCurrentEvalTask(task);
    setEvalModalVisible(true);
    evalForm.setFieldsValue({
      name: `${task.name}-数据评估`,
      taskType: task.synthesis_type || "QA",
      evalMethod: "AUTO",
    });
    // 懒加载模型列表
    if (!models.length) {
      loadModels();
    }
  };

  const loadModels = async () => {
    try {
      setModelLoading(true);
      const { data } = await queryModelListUsingGet({ page: 0, size: 1000 });
      setModels(data?.content || []);
    } catch (e) {
      console.error(e);
      message.error("获取模型列表失败");
    } finally {
      setModelLoading(false);
    }
  };

  const chatModelOptions = models
    .filter((m) => m.type === "CHAT")
    .map((m) => ({
      label: `${m.modelName} (${m.provider})`,
      value: m.id,
    }));

  const handleCreateEvaluation = async () => {
    if (!currentEvalTask) return;
    try {
      const values = await evalForm.validateFields();
      setEvalLoading(true);
      const taskType = currentEvalTask.synthesis_type || "QA";
      const payload = {
        name: values.name,
        taskType,
        evalMethod: values.evalMethod,
        sourceType: "SYNTHESIS",
        sourceId: currentEvalTask.id,
        sourceName: currentEvalTask.name,
        evalConfig: {
          modelId: values.modelId,
          dimensions: [
            {
              dimension: "问题是否独立",
              description:
                "仅分析问题，问题的主体和客体都比较明确，即使有省略，也符合语言习惯。在不需要补充其他信息的情况下不会引起疑惑。",
            },
            {
              dimension: "语法是否错误",
              description:
                "问题为疑问句，答案为陈述句; 不存在词语搭配不当的情况;连接词和标点符号不存在错用情况；逻辑混乱的情况不存在；语法结构都正确且完整。",
            },
            {
              dimension: "回答是否有针对性",
              description:
                "回答应对问题中的所有疑问点提供正面、直接的回答，不应引起疑惑。同时，答案不应有任何内容的遗漏，需构成一个完整的陈述。",
            },
          ],
        },
      };
      await createEvaluationTaskUsingPost(payload);
      message.success("评估任务创建成功");
      setEvalModalVisible(false);
      setCurrentEvalTask(null);
      evalForm.resetFields();
    } catch (error) {
      const err = error as { errorFields?: unknown; response?: { data?: { message?: string } } };
      if (err?.errorFields) return; // 表单校验错误
      message.error(err?.response?.data?.message || "评估任务创建失败");
    } finally {
      setEvalLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* 搜索和筛选 */}
      <SearchControls
        searchTerm={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="搜索任务名称..."
        filters={[
          {
            key: "status",
            label: "类型",
            options: [
              { label: "全部类型", value: "all" },
              { label: "问答对生成", value: "QA" },
              { label: "链式推理生成", value: "COT" },
            ],
          },
        ]}
        selectedFilters={{ status: [filterStatus] }}
        onFiltersChange={(filters) => {
          setFilterStatus(filters.status?.[0] || "all");
        }}
        showFilters
        showViewToggle={false}
      />
      {/* 任务表格 */}
      <Card>
        <Table
          columns={taskColumns}
          dataSource={tasks}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: total,
            onChange: (p, ps) => {
              setPage(p);
              setPageSize(ps);
            },
            showSizeChanger: true,
          }}
          scroll={{ x: "max-content" }}
          locale={{
            emptyText: (
              <div className="text-center py-12">
                <Sparkles className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <h3 className="text-base font-semibold text-gray-900 mb-2">
                  暂无合成任务
                </h3>
                <p className="text-gray-500 mb-4 text-sm">
                  {searchQuery
                    ? "没有找到匹配的任务"
                    : "开始创建您的第一个合成任务"}
                </p>
                {!searchQuery && filterStatus === "all" && (
                  <Button
                    onClick={() => navigate("/data/synthesis/task/create")}
                    className="bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 shadow-lg"
                  >
                    <Plus className="w-3 h-3 mr-1" />
                    创建合成任务
                  </Button>
                )}
              </div>
            ),
          }}
        />
      </Card>

      <Modal
        title="创建评估任务"
        open={evalModalVisible}
        onCancel={() => {
          setEvalModalVisible(false);
          setCurrentEvalTask(null);
          evalForm.resetFields();
        }}
        onOk={handleCreateEvaluation}
        confirmLoading={evalLoading}
        okText="开始评估"
        cancelText="取消"
      >
        <Form
          form={evalForm}
          layout="vertical"
          initialValues={{
            evalMethod: "AUTO",
          }}
        >
          <Form.Item
            label="评估任务名称"
            name="name"
            rules={[{ required: true, message: "请输入评估任务名称" }]}
          >
            <Input placeholder="例如：数据评估" />
          </Form.Item>
          <Form.Item
            label="任务类型"
            name="taskType"
          >
            <Select
              disabled
              options={[
                {
                  label:
                    currentEvalTask?.synthesis_type === "COT"
                      ? "COT评估"
                      : "QA评估",
                  value: currentEvalTask?.synthesis_type || "QA",
                },
              ]}
            />
          </Form.Item>
          <Form.Item
            label="评估方式"
            name="evalMethod"
            rules={[{ required: true, message: "请选择评估方式" }]}
          >
            <Select
              options={[
                { label: "模型自动评估", value: "AUTO" },
              ]}
            />
          </Form.Item>
          <Form.Item
            label="评估模型"
            name="modelId"
            rules={[{ required: true, message: "请选择评估模型" }]}
          >
            <Select
              placeholder={modelLoading ? "加载模型中..." : "请选择用于评估的模型"}
              loading={modelLoading}
              options={chatModelOptions}
              showSearch
              optionFilterProp="label"
            />
          </Form.Item>
          {currentEvalTask && (
            <Form.Item label="评估对象">
              <div className="text-xs text-gray-500">
                源类型：合成任务（SYNTHESIS）<br />
                源名称：{currentEvalTask.name}
              </div>
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
}
