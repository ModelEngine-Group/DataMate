import { useState } from "react";
import {
  Button,
  Card,
  Input,
  Select,
  Badge,
  Progress,
  Checkbox,
  Switch,
  Form,
  Divider,
  message,
} from "antd";
import {
  ArrowLeft,
  Play,
  Search as SearchIcon,
  Database,
  BarChart3,
  Shuffle,
  PieChart,
} from "lucide-react";
import type { RatioConfig, RatioTask } from "@/pages/RatioTask/ratio";
import { mockRatioTasks } from "@/mock/ratio";
import type { Dataset } from "@/pages/DataManagement/dataset.model";
import { useNavigate } from "react-router";
import DevelopmentInProgress from "@/components/DevelopmentInProgress";

const { TextArea } = Input;
const { Option } = Select;

export default function CreateRatioTask() {
  return <DevelopmentInProgress showTime="2025.11.30" />;

  const navigate = useNavigate();
  const [form] = Form.useForm();
  // 配比任务相关状态
  const [ratioTaskForm, setRatioTaskForm] = useState({
    name: "",
    description: "",
    ratioType: "dataset" as "dataset" | "label",
    selectedDatasets: [] as string[],
    ratioConfigs: [] as RatioConfig[],
    totalTargetCount: 10000,
    autoStart: true,
  });

  const [tasks, setTasks] = useState<RatioTask[]>(mockRatioTasks);
  const [datasets] = useState<Dataset[]>([]);

  const handleCreateRatioTask = async () => {
    try {
      const values = await form.validateFields();
      if (!ratioTaskForm.ratioConfigs.length) {
        message.error("请配置配比项");
        return;
      }
      const newTask: RatioTask = {
        id: Date.now(),
        name: values.name,
        status: ratioTaskForm.autoStart ? "pending" : "paused",
        progress: 0,
        sourceDatasets: ratioTaskForm.selectedDatasets,
        targetCount: values.totalTargetCount,
        generatedCount: 0,
        createdAt: new Date().toISOString().split("T")[0],
        ratioType: ratioTaskForm.ratioType,
        estimatedTime: "预计 20 分钟",
        ratioConfigs: ratioTaskForm.ratioConfigs,
      };

      setTasks([newTask, ...tasks]);
      setRatioTaskForm({
        name: "",
        description: "",
        ratioType: "dataset",
        selectedDatasets: [],
        ratioConfigs: [],
        totalTargetCount: 10000,
        autoStart: true,
      });
      form.resetFields();
      message.success("配比任务创建成功");
      navigate("/data/ratio-task");
    } catch {
      // 校验失败
    }
  };

  const handleDatasetSelection = (datasetId: string, checked: boolean) => {
    if (checked) {
      setRatioTaskForm((prev) => ({
        ...prev,
        selectedDatasets: [...prev.selectedDatasets, datasetId],
      }));
    } else {
      setRatioTaskForm((prev) => ({
        ...prev,
        selectedDatasets: prev.selectedDatasets.filter(
          (id) => id !== datasetId
        ),
        ratioConfigs: prev.ratioConfigs.filter(
          (config) => config.source !== datasetId
        ),
      }));
    }
  };

  const updateRatioConfig = (source: string, quantity: number) => {
    setRatioTaskForm((prev) => {
      const existingIndex = prev.ratioConfigs.findIndex(
        (config) => config.source === source
      );
      const totalOtherQuantity = prev.ratioConfigs
        .filter((config) => config.source !== source)
        .reduce((sum, config) => sum + config.quantity, 0);

      const newConfig: RatioConfig = {
        id: source,
        name: source,
        type: prev.ratioType,
        quantity: Math.min(
          quantity,
          prev.totalTargetCount - totalOtherQuantity
        ),
        percentage: Math.round((quantity / prev.totalTargetCount) * 100),
        source,
      };

      if (existingIndex >= 0) {
        const newConfigs = [...prev.ratioConfigs];
        newConfigs[existingIndex] = newConfig;
        return { ...prev, ratioConfigs: newConfigs };
      } else {
        return { ...prev, ratioConfigs: [...prev.ratioConfigs, newConfig] };
      }
    });
  };

  const generateAutoRatio = () => {
    const selectedCount = ratioTaskForm.selectedDatasets.length;
    if (selectedCount === 0) return;

    const baseQuantity = Math.floor(
      ratioTaskForm.totalTargetCount / selectedCount
    );
    const remainder = ratioTaskForm.totalTargetCount % selectedCount;

    const newConfigs: RatioConfig[] = ratioTaskForm.selectedDatasets.map(
      (datasetId, index) => {
        const quantity = baseQuantity + (index < remainder ? 1 : 0);
        return {
          id: datasetId,
          name: datasetId,
          type: ratioTaskForm.ratioType,
          quantity,
          percentage: Math.round(
            (quantity / ratioTaskForm.totalTargetCount) * 100
          ),
          source: datasetId,
        };
      }
    );

    setRatioTaskForm((prev) => ({ ...prev, ratioConfigs: newConfigs }));
  };

  const handleValuesChange = (_, allValues) => {
    setRatioTaskForm({ ...ratioTaskForm, ...allValues });
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <Button
            type="text"
            onClick={() => navigate("/data/synthesis/ratio-task")}
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
          </Button>
          <h1 className="text-xl font-bold bg-clip-text">创建配比任务</h1>
        </div>
      </div>
      <Card className="overflow-y-auto p-2">
        <Form
          form={form}
          initialValues={ratioTaskForm}
          onValuesChange={handleValuesChange}
          layout="vertical"
        >
          <div className="grid grid-cols-12 gap-6">
            {/* 左侧：数据集选择 */}
            <div className="col-span-5">
              <h2 className="font-medium text-gray-900 text-lg mb-2 flex items-center gap-2">
                <Database className="w-5 h-5" />
                数据集选择
              </h2>
              <Card>
                <div className="flex items-center gap-4 mb-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm">配比方式:</span>
                    <Form.Item name="ratioType" noStyle>
                      <Select
                        style={{ width: 120 }}
                        onChange={(value: "dataset" | "label") =>
                          setRatioTaskForm({
                            ...ratioTaskForm,
                            ratioType: value,
                            ratioConfigs: [],
                          })
                        }
                      >
                        <Option value="dataset">按数据集</Option>
                        <Option value="label">按标签</Option>
                      </Select>
                    </Form.Item>
                  </div>
                  <Input
                    prefix={<SearchIcon className="text-gray-400" />}
                    placeholder="搜索数据集"
                    style={{ width: 180 }}
                    // 可加搜索逻辑
                  />
                </div>
                <div style={{ maxHeight: 500, overflowY: "auto" }}>
                  {datasets.map((dataset) => (
                    <Card
                      key={dataset.id}
                      size="small"
                      className={`mb-2 cursor-pointer ${
                        ratioTaskForm.selectedDatasets.includes(dataset.id)
                          ? "border-blue-500"
                          : "hover:border-blue-200"
                      }`}
                      onClick={() =>
                        handleDatasetSelection(
                          dataset.id,
                          !ratioTaskForm.selectedDatasets.includes(dataset.id)
                        )
                      }
                    >
                      <div className="flex items-start gap-3">
                        <Checkbox
                          checked={ratioTaskForm.selectedDatasets.includes(
                            dataset.id
                          )}
                          onChange={(e) =>
                            handleDatasetSelection(dataset.id, e.target.checked)
                          }
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-sm truncate">
                              {dataset.name}
                            </span>
                            <Badge color="blue">{dataset.type}</Badge>
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {dataset.description}
                          </div>
                          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                            <span>{dataset.records?.toLocaleString()}条</span>
                            <span>{dataset.size}</span>
                            <span>{dataset.format}</span>
                          </div>
                          {ratioTaskForm.ratioType === "label" &&
                            dataset.labels && (
                              <div className="flex flex-wrap gap-1 mt-2">
                                {dataset.labels.map((label, index) => (
                                  <Badge key={index} color="gray">
                                    {label}
                                  </Badge>
                                ))}
                              </div>
                            )}
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg mt-4">
                  <span className="text-sm text-gray-600">
                    已选择 {ratioTaskForm.selectedDatasets.length} 个数据集
                  </span>
                  <Button
                    size="small"
                    onClick={() =>
                      setRatioTaskForm({
                        ...ratioTaskForm,
                        selectedDatasets: [],
                        ratioConfigs: [],
                      })
                    }
                  >
                    清空选择
                  </Button>
                </div>
              </Card>
            </div>
            {/* 右侧：配比配置 */}
            <div className="col-span-7">
              <h2 className="font-medium text-gray-900 text-lg mb-2 flex items-center gap-2">
                <PieChart className="w-5 h-5" />
                配比配置
              </h2>
              <Card>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <span className="flex items-center gap-2 font-semibold">
                      <BarChart3 className="w-5 h-5" />
                      配比设置
                    </span>
                    <div className="text-gray-500 text-xs">
                      设置每个数据集的配比数量
                    </div>
                  </div>
                  <Button
                    icon={<Shuffle />}
                    size="small"
                    onClick={generateAutoRatio}
                    disabled={ratioTaskForm.selectedDatasets.length === 0}
                  >
                    平均分配
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <Form.Item
                    label="任务名称"
                    name="name"
                    rules={[{ required: true, message: "请输入配比任务名称" }]}
                  >
                    <Input
                      placeholder="输入配比任务名称"
                      value={ratioTaskForm.name}
                    />
                  </Form.Item>
                  <Form.Item
                    label="目标总数量"
                    name="totalTargetCount"
                    rules={[{ required: true, message: "请输入目标总数量" }]}
                  >
                    <Input
                      type="number"
                      placeholder="目标总数量"
                      min={1}
                      value={ratioTaskForm.totalTargetCount}
                    />
                  </Form.Item>
                </div>
                <Form.Item label="任务描述" name="description">
                  <TextArea
                    placeholder="描述配比任务的目的和要求（可选）"
                    rows={2}
                    value={ratioTaskForm.description}
                  />
                </Form.Item>
                <div className="mb-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">配比设置</span>
                    <span className="text-xs text-gray-500">
                      已配置:{" "}
                      {ratioTaskForm.ratioConfigs.reduce(
                        (sum, config) => sum + config.quantity,
                        0
                      )}{" "}
                      / {ratioTaskForm.totalTargetCount}
                    </span>
                  </div>
                  {ratioTaskForm.selectedDatasets.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <BarChart3 className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                      <p className="text-sm">请先选择数据集</p>
                    </div>
                  ) : (
                    <div style={{ maxHeight: 500, overflowY: "auto" }}>
                      {ratioTaskForm.selectedDatasets.map((datasetId) => {
                        const dataset = datasets.find(
                          (d) => d.id === datasetId
                        );
                        const config = ratioTaskForm.ratioConfigs.find(
                          (c) => c.source === datasetId
                        );
                        const currentQuantity = config?.quantity || 0;
                        if (!dataset) return null;
                        return (
                          <Card key={datasetId} size="small" className="mb-2">
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-sm">
                                  {dataset.name}
                                </span>
                                <Badge color="gray">
                                  {dataset.records.toLocaleString()}条
                                </Badge>
                              </div>
                              <div className="text-xs text-gray-500">
                                {config?.percentage || 0}%
                              </div>
                            </div>
                            {ratioTaskForm.ratioType === "dataset" ? (
                              <div>
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="text-xs">数量:</span>
                                  <Input
                                    type="number"
                                    value={currentQuantity}
                                    onChange={(e) =>
                                      updateRatioConfig(
                                        datasetId,
                                        Number(e.target.value)
                                      )
                                    }
                                    style={{ width: 80 }}
                                    min={0}
                                    max={ratioTaskForm.totalTargetCount}
                                  />
                                  <span className="text-xs text-gray-500">
                                    条
                                  </span>
                                </div>
                                <Progress
                                  percent={Math.round(
                                    (currentQuantity /
                                      ratioTaskForm.totalTargetCount) *
                                      100
                                  )}
                                  size="small"
                                />
                              </div>
                            ) : (
                              <div>
                                {dataset.labels?.map((label, index) => {
                                  const labelConfig =
                                    ratioTaskForm.ratioConfigs.find(
                                      (c) =>
                                        c.source === `${datasetId}_${label}`
                                    );
                                  const labelQuantity =
                                    labelConfig?.quantity || 0;
                                  return (
                                    <div
                                      key={index}
                                      className="flex items-center gap-2 mb-2"
                                    >
                                      <Badge color="gray">{label}</Badge>
                                      <Input
                                        type="number"
                                        value={labelQuantity}
                                        onChange={(e) =>
                                          updateRatioConfig(
                                            `${datasetId}_${label}`,
                                            Number(e.target.value)
                                          )
                                        }
                                        style={{ width: 70 }}
                                        min={0}
                                      />
                                      <span className="text-xs text-gray-500">
                                        条
                                      </span>
                                      <Progress
                                        percent={Math.round(
                                          (labelQuantity /
                                            ratioTaskForm.totalTargetCount) *
                                            100
                                        )}
                                        size="small"
                                        style={{ width: 80 }}
                                      />
                                      <span className="text-xs text-gray-500 min-w-8">
                                        {Math.round(
                                          (labelQuantity /
                                            ratioTaskForm.totalTargetCount) *
                                            100
                                        )}
                                        %
                                      </span>
                                    </div>
                                  );
                                })}
                              </div>
                            )}
                          </Card>
                        );
                      })}
                    </div>
                  )}
                </div>
                {/* 配比预览 */}
                {ratioTaskForm.ratioConfigs.length > 0 && (
                  <div className="mb-4">
                    <span className="text-sm font-medium">配比预览</span>
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">总配比数量:</span>
                          <span className="ml-2 font-medium">
                            {ratioTaskForm.ratioConfigs
                              .reduce((sum, config) => sum + config.quantity, 0)
                              .toLocaleString()}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">目标数量:</span>
                          <span className="ml-2 font-medium">
                            {ratioTaskForm.totalTargetCount.toLocaleString()}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">配比项目:</span>
                          <span className="ml-2 font-medium">
                            {ratioTaskForm.ratioConfigs.length}个
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">预计时间:</span>
                          <span className="ml-2 font-medium">约 20 分钟</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div className="flex items-center justify-between p-3 border rounded-lg mb-4">
                  <div>
                    <span className="text-sm font-medium">创建后自动开始</span>
                    <div className="text-xs text-gray-500 mt-1">
                      任务创建完成后立即开始执行
                    </div>
                  </div>
                  <Form.Item name="autoStart" valuePropName="checked" noStyle>
                    <Switch
                      checked={ratioTaskForm.autoStart}
                      onChange={(checked) =>
                        setRatioTaskForm({
                          ...ratioTaskForm,
                          autoStart: checked,
                        })
                      }
                    />
                  </Form.Item>
                </div>
                <Divider />
                <div className="flex justify-end gap-2">
                  <Button
                    onClick={() => navigate("/data/synthesis/ratio-task")}
                  >
                    取消
                  </Button>
                  <Button
                    type="primary"
                    onClick={handleCreateRatioTask}
                    disabled={
                      !ratioTaskForm.name ||
                      ratioTaskForm.ratioConfigs.length === 0
                    }
                  >
                    <Play className="w-4 h-4 mr-2" />
                    创建任务
                  </Button>
                </div>
              </Card>
            </div>
          </div>
        </Form>
      </Card>
    </div>
  );
}
