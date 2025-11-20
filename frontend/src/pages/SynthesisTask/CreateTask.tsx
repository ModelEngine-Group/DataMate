import { useEffect, useState } from "react";
import type { Dataset } from "@/pages/DataManagement/dataset.model";
import {
  Steps,
  Card,
  Select,
  Input,
  Checkbox,
  Button,
  Badge,
  Divider,
  Radio,
  Form,
  message,
} from "antd";
import {
  Eye,
  Trash2,
  Settings,
  ArrowLeft,
  ArrowRight,
  Play,
  Edit,
  Copy,
  Save,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Search,
  CheckCircle,
  Code,
  X,
  MoreHorizontal,
  Activity,
  MessageSquare,
  Brain,
} from "lucide-react";
import { Link, useNavigate } from "react-router";
import { queryDatasetsUsingGet } from "../DataManagement/dataset.api";
import { formatBytes } from "@/utils/unit";
import DatasetFileTransfer from "../KnowledgeBase/components/DatasetFileTransfer";

const { TextArea } = Input;

export default function SynthesisTaskCreate() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [searchQuery, setSearchQuery] = useState("");
  const [createStep, setCreateStep] = useState(1);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [selectedMap, setSelectedMap] = useState<Record<string, DatasetFile[]>>(
    {}
  );
  const [files] = useState<File[]>([]);
  const [selectedSynthesisTypes, setSelectedSynthesisTypes] = useState<
    string[]
  >(["qa_judge"]);
  const [showDebugCard, setShowDebugCard] = useState(false);
  const [debugStepId, setDebugStepId] = useState<string | null>(null);
  const [expandedTypes, setExpandedTypes] = useState<string[]>([
    "qa",
    "distillation",
  ]);

  const fetchDatasets = async () => {
    const { data } = await queryDatasetsUsingGet({ page: 1, size: 1000 });
    setDatasets(data.content || []);
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  // 表单数据
  const [formValues, setFormValues] = useState({
    name: "",
    sourceDataset: "",
    targetCount: 1000,
    description: "",
    executionMode: "immediate",
    scheduleStrategy: "",
    outputPath: "",
    enableQualityCheck: false,
    enableNotification: false,
  });

  const synthesisTypes = [
    {
      id: "qa",
      name: "生成问答对",
      icon: MessageSquare,
      count: 14,
      expanded: true,
      description: "基于文本生成各类问答对",
      children: [
        {
          id: "qa_judge",
          name: "文字生成问答对_判断题",
          count: 1,
          description: "生成判断题形式的问答对",
        },
        {
          id: "qa_choice",
          name: "文字生成问答对_选择题",
          count: 0,
          description: "生成多选题形式的问答对",
        },
        {
          id: "qa_fill",
          name: "文字生成问答对_填空题",
          count: 0,
          description: "生成填空题形式的问答对",
        },
        {
          id: "qa_short",
          name: "相关文本描述问答对_金融领域",
          count: 0,
          description: "金融领域的专业问答对",
        },
      ],
    },
    {
      id: "distillation",
      name: "生成蒸馏",
      icon: Brain,
      count: 6,
      expanded: true,
      description: "知识蒸馏数据生成",
      children: [
        {
          id: "dist_text",
          name: "相关文本生成蒸馏",
          count: 0,
          description: "基于文本的知识蒸馏",
        },
        {
          id: "dist_qa",
          name: "问答数据",
          count: 0,
          description: "问答形式的蒸馏数据",
        },
        {
          id: "dist_instruct",
          name: "相关指令生成蒸馏问题_few-shot",
          count: 0,
          description: "Few-shot指令蒸馏",
        },
        {
          id: "dist_summary",
          name: "问答数据为基础蒸馏",
          count: 0,
          description: "基于问答数据的蒸馏",
        },
        {
          id: "dist_reasoning",
          name: "问答数据为基础高质量",
          count: 0,
          description: "高质量推理数据蒸馏",
        },
      ],
    },
  ];

  const toggleTypeExpansion = (typeId: string) => {
    setExpandedTypes((prev) =>
      prev.includes(typeId)
        ? prev.filter((id) => id !== typeId)
        : [...prev, typeId]
    );
  };

  const handleSynthesisTypeSelect = (typeId: string) => {
    setSelectedSynthesisTypes((prev) => {
      if (prev.includes(typeId)) {
        return prev.filter((id) => id !== typeId);
      } else {
        return [...prev, typeId];
      }
    });
  };

  const handleValuesChange = (_, allValues) => {
    setFormValues({ ...formValues, ...allValues });
  };

  const handleSelectAllFiles = () => {
    const filteredFiles = files.filter((file) =>
      file.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
    if (selectedFiles.length === filteredFiles.length) {
      setSelectedFiles([]);
    } else {
      setSelectedFiles(filteredFiles.map((file) => file.id));
    }
  };

  const handleRemoveSelectedFile = (fileId: string) => {
    setSelectedFiles(selectedFiles.filter((id) => id !== fileId));
  };

  const handleCreateTask = async () => {
    try {
      const values = await form.validateFields();
      if (
        !values.name ||
        !values.sourceDataset ||
        selectedFiles.length === 0 ||
        selectedSynthesisTypes.length === 0 ||
        !values.outputPath ||
        !values.targetCount ||
        (values.executionMode === "scheduled" && !values.scheduleStrategy)
      ) {
        message.error("请填写所有必填项");
        return;
      }

      const newTask: SynthesisTask = {
        id: Date.now(),
        name: values.name,
        type: selectedSynthesisTypes[0].includes("qa") ? "qa" : "distillation",
        status: values.executionMode === "immediate" ? "pending" : "paused",
        progress: 0,
        sourceDataset: values.sourceDataset,
        targetCount: values.targetCount,
        generatedCount: 0,
        createdAt: new Date().toISOString().split("T")[0],
        template: "自动生成模板",
        estimatedTime: "预计 30 分钟",
      };

      setTasks([newTask, ...tasks]);
      setShowCreateTask(false);
      setCreateStep(1);

      // Reset form
      form.resetFields();
      setSelectedFiles([]);

      // Auto-start simulation if immediate execution
      if (values.executionMode === "immediate") {
        setTimeout(() => {
          setTasks((prev) =>
            prev.map((task) =>
              task.id === newTask.id ? { ...task, status: "running" } : task
            )
          );

          const interval = setInterval(() => {
            setTasks((prev) =>
              prev.map((task) => {
                if (task.id === newTask.id && task.status === "running") {
                  const newProgress = Math.min(
                    task.progress + Math.random() * 8 + 2,
                    100
                  );
                  const isCompleted = newProgress >= 100;
                  return {
                    ...task,
                    progress: newProgress,
                    generatedCount: Math.floor(
                      (newProgress / 100) * task.targetCount
                    ),
                    status: isCompleted ? "completed" : "running",
                    estimatedTime: isCompleted
                      ? "已完成"
                      : `剩余 ${Math.ceil((100 - newProgress) / 10)} 分钟`,
                  };
                }
                return task;
              })
            );
          }, 1000);

          setTimeout(() => clearInterval(interval), 12000);
        }, 1000);
      }
    } catch {
      // 校验失败
    }
  };

  const renderCreateTaskPage = () => {
    if (createStep === 1) {
      return (
        <div className="flex-1 p-4 overflow-auto">
          <Form
            form={form}
            layout="vertical"
            initialValues={formValues}
            onValuesChange={handleValuesChange}
            autoComplete="off"
          >
            <h2 className="font-medium text-gray-900 text-lg mb-2">基本信息</h2>
            <Form.Item
              label="任务名称"
              name="name"
              rules={[{ required: true, message: "请输入任务名称" }]}
            >
              <Input placeholder="输入任务名称" className="h-9 text-sm" />
            </Form.Item>
            <Form.Item
              label="目标生成数量"
              name="targetCount"
              rules={[{ required: true, message: "请输入目标生成数量" }]}
            >
              <Input
                type="number"
                min={1}
                placeholder="输入目标生成数量"
                className="h-9 text-sm"
              />
            </Form.Item>
            <Form.Item label="任务描述" name="description">
              <TextArea
                placeholder="描述任务的目的和要求（可选）"
                rows={3}
                className="resize-none text-sm"
              />
            </Form.Item>
            <DatasetFileTransfer
              open
              selectedMap={selectedMap}
              onSelectedChange={setSelectedMap}
            />
            <h2 className="font-medium text-gray-900 text-lg mt-6 mb-2">
              任务配置
            </h2>
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-4">
                <Form.Item
                  label="执行方式"
                  name="executionMode"
                  rules={[{ required: true, message: "请选择执行方式" }]}
                >
                  <Radio.Group
                    options={[
                      { label: "立即执行", value: "immediate" },
                      { label: "周期执行", value: "scheduled" },
                    ]}
                    optionType="button"
                    buttonStyle="solid"
                  />
                </Form.Item>
                {form.getFieldValue("executionMode") === "scheduled" && (
                  <Form.Item
                    label="执行策略"
                    name="scheduleStrategy"
                    rules={[{ required: true, message: "请选择执行策略" }]}
                  >
                    <Select
                      placeholder="选择执行策略"
                      options={[
                        { label: "每日执行", value: "daily" },
                        { label: "每周执行", value: "weekly" },
                        { label: "每月执行", value: "monthly" },
                        { label: "自定义周期", value: "custom" },
                      ]}
                    />
                  </Form.Item>
                )}
              </div>
              <div className="space-y-4">
                <Form.Item
                  label="存放路径"
                  name="outputPath"
                  rules={[{ required: true, message: "请输入存放路径" }]}
                >
                  <Input
                    placeholder="输入结果存放路径，如：/data/synthesis/output"
                    className="h-9 text-sm"
                  />
                </Form.Item>
                <p className="text-xs text-gray-500">
                  指定合成结果的存储位置，支持本地路径和云存储路径
                </p>
                <Form.Item name="enableQualityCheck" valuePropName="checked">
                  <Checkbox>
                    启用质量检查（对合成结果进行自动质量评估）
                  </Checkbox>
                </Form.Item>
                <Form.Item name="enableNotification" valuePropName="checked">
                  <Checkbox>
                    发送完成通知（任务完成后发送邮件或消息通知）
                  </Checkbox>
                </Form.Item>
              </div>
            </div>
          </Form>
        </div>
      );
    }

    if (createStep === 2) {
      return (
        <div className="">
          <div className="grid grid-cols-12 gap-6 min-h-[500px]">
            {/* 左侧合成指令 */}
            <div className="col-span-4 space-y-4">
              <Card className="shadow-sm border-0 bg-white">
                <h1 className="text-base">合成指令</h1>
                <div className="space-y-3 mb-4">
                  <div className="relative">
                    <Search className="w-3 h-3 absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <Input
                      placeholder="搜索名称、分类搜索"
                      className="pl-7 text-xs h-8"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  {synthesisTypes.map((type) => {
                    return (
                      <div key={type.id} className="space-y-1">
                        <div
                          className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors"
                          onClick={() => toggleTypeExpansion(type.id)}
                        >
                          <div className="w-5 h-5 bg-green-500 rounded-lg flex items-center justify-center shadow-sm">
                            {expandedTypes.includes(type.id) ? (
                              <ChevronDown className="w-3 h-3 text-white" />
                            ) : (
                              <ChevronRight className="w-3 h-3 text-white" />
                            )}
                          </div>
                          <span className="font-medium text-xs">
                            {type.name}({type.count})
                          </span>
                        </div>

                        {expandedTypes.includes(type.id) && (
                          <div className="ml-7 space-y-1">
                            {type.children.map((child) => (
                              <div
                                key={child.id}
                                className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer text-xs transition-colors ${
                                  selectedSynthesisTypes.includes(child.id)
                                    ? "bg-blue-50 text-blue-700 border border-blue-200"
                                    : "hover:bg-gray-50"
                                }`}
                                onClick={() =>
                                  handleSynthesisTypeSelect(child.id)
                                }
                              >
                                <Checkbox
                                  checked={selectedSynthesisTypes.includes(
                                    child.id
                                  )}
                                  onChange={() =>
                                    handleSynthesisTypeSelect(child.id)
                                  }
                                />
                                <span className="flex-1">{child.name}</span>
                                <span className="text-gray-400">
                                  ({child.count})
                                </span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </Card>
            </div>

            {/* 右侧合成编排 */}
            <div className="col-span-8">
              <Card className="h-full shadow-sm border-0 bg-white">
                <div className="flex items-center justify-between">
                  <h1>合成步骤编排({selectedSynthesisTypes.length})</h1>
                  <div className="flex items-center gap-2">
                    <Button className="hover:bg-white text-xs" type="default">
                      <RefreshCw className="w-3 h-3 mr-1" />
                      选择合成模板
                    </Button>
                    <Button className="hover:bg-white text-xs" type="default">
                      <Eye className="w-3 h-3 mr-1" />
                      启用调测
                    </Button>
                  </div>
                </div>
                <div className="space-y-4">
                  {/* 开始节点 */}
                  <div className="relative">
                    <Card className="border-green-200 bg-green-50 shadow-sm">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-xs font-medium shadow-lg">
                          开
                        </div>
                        <span className="font-medium text-sm">开始</span>
                      </div>
                    </Card>
                  </div>

                  {/* 合成步骤 */}
                  {selectedSynthesisTypes.map((typeId, index) => {
                    const typeInfo = synthesisTypes
                      .flatMap((t) => t.children)
                      .find((c) => c.id === typeId);
                    if (!typeInfo) return null;

                    return (
                      <div key={typeId} className="relative">
                        <div className="absolute -top-4 left-4 w-px h-4 bg-gray-300"></div>
                        <Card className="border-blue-200 bg-blue-50 shadow-sm">
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-medium shadow-lg">
                              {index + 1}
                            </div>
                            <div className="flex-1 space-y-3">
                              <div className="flex items-center justify-between">
                                <span className="font-medium text-sm">
                                  {typeInfo.name}
                                </span>
                                <div className="flex items-center gap-1">
                                  <Button
                                    className="hover:bg-white p-1"
                                    type="text"
                                  >
                                    <Copy className="w-3 h-3" />
                                  </Button>
                                  <Button
                                    className="hover:bg-white p-1"
                                    type="text"
                                  >
                                    <Edit className="w-3 h-3" />
                                  </Button>
                                  <Button
                                    className="hover:bg-white p-1"
                                    type="text"
                                  >
                                    <Trash2 className="w-3 h-3" />
                                  </Button>
                                  <Button
                                    className="hover:bg-white p-1"
                                    type="text"
                                  >
                                    <MoreHorizontal className="w-3 h-3" />
                                  </Button>
                                </div>
                              </div>

                              <div className="text-xs text-gray-600 bg-white p-2 rounded-lg border">
                                该任务为从用户提供的参考文本中抽取出一个判断题，同时输出正确答案。
                              </div>

                              <div className="grid grid-cols-2 gap-3">
                                <div>
                                  <span className="text-xs font-medium text-gray-600">
                                    模型
                                  </span>
                                  <Select
                                    defaultValue="未选择"
                                    options={[
                                      { label: "GPT-4", value: "gpt-4" },
                                      { label: "GPT-3.5", value: "gpt-3.5" },
                                    ]}
                                  ></Select>
                                </div>
                                <div>
                                  <span className="text-xs font-medium text-gray-600">
                                    配置参数
                                  </span>
                                  <Button
                                    className="h-7 w-full mt-1 bg-white hover:bg-gray-50 text-xs"
                                    type="default"
                                    onClick={() => {
                                      setDebugStepId(typeId);
                                      setShowDebugCard(true);
                                    }}
                                  >
                                    配置参数
                                  </Button>
                                </div>
                              </div>

                              <div>
                                <span className="text-xs font-medium text-gray-600">
                                  指令
                                </span>
                                <div className="text-xs text-gray-500 mt-1 bg-white p-2 rounded border">
                                  该任务为从用户提供的参考文本中抽取出一个判断题，同时输出正确答案。
                                </div>
                              </div>

                              <div className="grid grid-cols-2 gap-3">
                                <div>
                                  <span className="text-xs font-medium text-gray-600">
                                    输入变量
                                  </span>
                                  <div className="flex items-center gap-1 mt-1">
                                    <Badge className="text-xs bg-white border border-gray-200">
                                      text 参考文本
                                    </Badge>
                                  </div>
                                </div>
                                <div>
                                  <span className="text-xs font-medium text-gray-600">
                                    输出变量
                                  </span>
                                  <div className="flex items-center gap-1 mt-1">
                                    <Badge className="text-xs bg-blue-100 text-blue-800">
                                      answer 回答
                                    </Badge>
                                    <Badge className="text-xs bg-blue-100 text-blue-800">
                                      question 问题
                                    </Badge>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </Card>
                      </div>
                    );
                  })}

                  {/* 结束节点 */}
                  <div className="relative">
                    <div className="absolute -top-4 left-4 w-px h-4 bg-gray-300"></div>
                    <Card className="border-gray-200 bg-gray-50 shadow-sm">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-gray-500 text-white rounded-full flex items-center justify-center text-xs font-medium shadow-lg">
                          结
                        </div>
                        <span className="font-medium text-sm">结束</span>
                      </div>
                    </Card>
                  </div>
                </div>

                <div className="flex justify-between pt-4 border-t">
                  <Button
                    onClick={() => setCreateStep(1)}
                    className="px-4 py-2 text-sm"
                    type="default"
                  >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    上一步
                  </Button>
                  <Button
                    onClick={handleCreateTask}
                    disabled={
                      !form.getFieldValue("name") ||
                      !form.getFieldValue("sourceDataset") ||
                      selectedFiles.length === 0 ||
                      selectedSynthesisTypes.length === 0 ||
                      !form.getFieldValue("outputPath") ||
                      !form.getFieldValue("targetCount") ||
                      (form.getFieldValue("executionMode") === "scheduled" &&
                        !form.getFieldValue("scheduleStrategy"))
                    }
                    className="px-6 py-2 text-sm font-semibold bg-purple-600 hover:bg-purple-700 shadow-lg"
                    type="primary"
                  >
                    <Play className="w-4 h-4 mr-2" />
                    创建任务
                  </Button>
                </div>
              </Card>
            </div>
          </div>

          {/* Debug Card */}
          {showDebugCard && debugStepId && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <Card className="w-full max-w-4xl max-h-[90vh] overflow-hidden shadow-2xl">
                <div className="flex items-center justify-between">
                  <div>
                    <Settings className="w-4 h-4" />
                    流程调测 -{" "}
                    {
                      synthesisTypes
                        .flatMap((t) => t.children)
                        .find((c) => c.id === debugStepId)?.name
                    }
                  </div>
                  <Button
                    onClick={() => {
                      setShowDebugCard(false);
                      setDebugStepId(null);
                    }}
                    className="hover:bg-white"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
                <div className="grid grid-cols-2 h-[70vh]">
                  {/* Left Panel - Configuration */}
                  <div className="border-r bg-gray-50 p-4 overflow-y-auto">
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-semibold text-base mb-3 flex items-center gap-2">
                          <Settings className="w-4 h-4" />
                          参数配置
                        </h4>

                        <div className="space-y-3">
                          <div className="space-y-1">
                            <span className="text-xs font-medium">
                              模型选择
                            </span>
                            <Select
                              defaultValue="gpt-4"
                              options={[
                                { label: "gpt-4", value: "GPT-4" },
                                {
                                  label: "gpt-3.5-turbo",
                                  value: "GPT-3.5 Turbo",
                                },
                                { label: "claude-3", value: "Claude-3" },
                              ]}
                            ></Select>
                          </div>
                          <div className="space-y-1">
                            <span className="text-xs font-medium">
                              Temperature
                            </span>
                            <div className="flex items-center gap-2">
                              <Input
                                type="number"
                                defaultValue="0.7"
                                min="0"
                                max="2"
                                step="0.1"
                                className="h-8 text-sm"
                              />
                              <span className="text-xs text-gray-500">
                                0.0-2.0
                              </span>
                            </div>
                          </div>
                          <div className="space-y-1">
                            <span className="text-xs font-medium">
                              Max Tokens
                            </span>
                            <Input
                              type="number"
                              defaultValue="1000"
                              min="1"
                              max="4000"
                              className="h-8 text-sm"
                            />
                          </div>
                          <div className="space-y-1">
                            <span className="text-xs font-medium">Top P</span>
                            <div className="flex items-center gap-2">
                              <Input
                                type="number"
                                defaultValue="1.0"
                                min="0"
                                max="1"
                                step="0.1"
                                className="h-8 text-sm"
                              />
                              <span className="text-xs text-gray-500">
                                0.0-1.0
                              </span>
                            </div>
                          </div>
                          <div className="space-y-1">
                            <span className="text-xs font-medium">
                              Frequency Penalty
                            </span>
                            <div className="flex items-center gap-2">
                              <Input
                                type="number"
                                defaultValue="0.0"
                                min="-2"
                                max="2"
                                step="0.1"
                                className="h-8 text-sm"
                              />
                              <span className="text-xs text-gray-500">
                                -2.0-2.0
                              </span>
                            </div>
                          </div>
                          <div className="space-y-1">
                            <span className="text-xs font-medium">
                              Presence Penalty
                            </span>
                            <div className="flex items-center gap-2">
                              <Input
                                type="number"
                                defaultValue="0.0"
                                min="-2"
                                max="2"
                                step="0.1"
                                className="h-8 text-sm"
                              />
                              <span className="text-xs text-gray-500">
                                -2.0-2.0
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <Divider />

                      <div>
                        <h4 className="font-semibold text-base mb-3 flex items-center gap-2">
                          <Code className="w-4 h-4" />
                          指令模板
                        </h4>

                        <div className="space-y-3">
                          <div className="space-y-1">
                            <span className="text-xs font-medium">
                              系统指令
                            </span>
                            <TextArea
                              defaultValue="你是一个专业的数据合成助手，请根据给定的文本内容生成高质量的判断题。"
                              rows={2}
                              className="resize-none text-xs"
                            />
                          </div>

                          <div className="space-y-1">
                            <span className="text-xs font-medium">
                              用户指令模板
                            </span>
                            <TextArea
                              defaultValue={`根据给定的文本内容，生成一个判断题。

文本内容：{text}

请按照以下格式生成：
1. 判断题：[基于文本内容的判断题]
2. 答案：[对/错]
3. 解释：[简要解释为什么这个答案是正确的]

要求：
- 判断题应该基于文本的核心内容
- 答案必须明确且有依据
- 解释要简洁清晰`}
                              rows={8}
                              className="resize-none text-xs font-mono"
                            />
                          </div>

                          <div className="space-y-1">
                            <span className="text-xs font-medium">
                              输入变量
                            </span>
                            <div className="flex flex-wrap gap-1">
                              <Badge className="bg-blue-50 text-blue-700 text-xs">
                                text
                              </Badge>
                            </div>
                          </div>

                          <div className="space-y-1">
                            <span className="text-xs font-medium">
                              输出变量
                            </span>
                            <div className="flex flex-wrap gap-1">
                              <Badge className="bg-green-50 text-green-700 text-xs">
                                question
                              </Badge>
                              <Badge className="bg-green-50 text-green-700 text-xs">
                                answer
                              </Badge>
                              <Badge className="bg-green-50 text-green-700 text-xs">
                                explanation
                              </Badge>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Right Panel - Testing */}
                  <div className="p-4 overflow-y-auto">
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-semibold text-base mb-3 flex items-center gap-2">
                          <Play className="w-4 h-4" />
                          调测验证
                        </h4>

                        <div className="space-y-3">
                          <div className="space-y-1">
                            <span className="text-xs font-medium">
                              测试输入
                            </span>
                            <TextArea
                              placeholder="输入测试文本内容..."
                              defaultValue="人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。"
                              rows={4}
                              className="resize-none text-xs"
                            />
                          </div>

                          <div className="flex gap-2">
                            <Button className="flex-1 bg-orange-500 hover:bg-orange-600 text-sm">
                              <Play className="w-3 h-3 mr-1" />
                              开始调测
                            </Button>
                            <Button className="text-sm bg-transparent">
                              <RefreshCw className="w-3 h-3 mr-1" />
                              重置
                            </Button>
                          </div>

                          <div className="space-y-1">
                            <span className="text-xs font-medium">
                              调测输出
                            </span>
                            <div className="bg-gray-50 border rounded-lg p-3 min-h-[150px]">
                              <div className="space-y-2 text-xs">
                                <div>
                                  <span className="font-medium text-gray-700">
                                    判断题：
                                  </span>
                                  <span className="text-gray-900">
                                    人工智能是计算机科学的一个分支。
                                  </span>
                                </div>
                                <div>
                                  <span className="font-medium text-gray-700">
                                    答案：
                                  </span>
                                  <Badge className="ml-1 bg-green-100 text-green-800 text-xs">
                                    对
                                  </Badge>
                                </div>
                                <div>
                                  <span className="font-medium text-gray-700">
                                    解释：
                                  </span>
                                  <span className="text-gray-900">
                                    根据文本内容，人工智能确实是计算机科学的一个分支，这是文本中明确提到的信息。
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="grid grid-cols-2 gap-3 text-xs">
                            <div className="space-y-1">
                              <span className="text-gray-500">响应时间</span>
                              <span className="font-semibold">1.2秒</span>
                            </div>
                            <div className="space-y-1">
                              <span className="text-gray-500">Token消耗</span>
                              <span className="font-semibold">156 tokens</span>
                            </div>
                            <div className="space-y-1">
                              <span className="text-gray-500">成功率</span>
                              <span className="font-semibold text-green-600">
                                100%
                              </span>
                            </div>
                            <div className="space-y-1">
                              <span className="text-gray-500">质量评分</span>
                              <span className="font-semibold text-blue-600">
                                95分
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <Divider />

                      <div>
                        <h4 className="font-semibold text-base mb-3 flex items-center gap-2">
                          <Activity className="w-4 h-4" />
                          批量测试
                        </h4>

                        <div className="space-y-3">
                          <div className="space-y-1">
                            <span className="text-xs font-medium">
                              测试样本数量
                            </span>
                            <Select
                              defaultValue="10"
                              options={[
                                { label: "5", value: "5个样本" },
                                { label: "10", value: "10个样本" },
                                { label: "20", value: "20个样本" },
                                { label: "50", value: "50个样本" },
                              ]}
                            ></Select>
                          </div>

                          <Button className="w-full bg-transparent text-sm">
                            <Activity className="w-3 h-3 mr-1" />
                            开始批量测试
                          </Button>

                          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                            <div className="flex items-center gap-2 mb-2">
                              <CheckCircle className="w-3 h-3 text-blue-600" />
                              <span className="text-xs font-medium text-blue-800">
                                批量测试结果
                              </span>
                            </div>
                            <div className="grid grid-cols-2 gap-3 text-xs">
                              <div>
                                <span className="text-blue-600">
                                  成功样本：
                                </span>
                                <span className="font-semibold text-blue-800">
                                  9/10
                                </span>
                              </div>
                              <div>
                                <span className="text-blue-600">
                                  平均质量：
                                </span>
                                <span className="font-semibold text-blue-800">
                                  92分
                                </span>
                              </div>
                              <div>
                                <span className="text-blue-600">
                                  平均耗时：
                                </span>
                                <span className="font-semibold text-blue-800">
                                  1.4秒
                                </span>
                              </div>
                              <div>
                                <span className="text-blue-600">总消耗：</span>
                                <span className="font-semibold text-blue-800">
                                  1,420 tokens
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="border-t p-4 bg-gray-50">
                  <div className="flex justify-between">
                    <Button className="text-sm bg-transparent">
                      <Save className="w-3 h-3 mr-1" />
                      保存配置
                    </Button>
                    <div className="flex gap-2">
                      <Button
                        onClick={() => {
                          setShowDebugCard(false);
                          setDebugStepId(null);
                        }}
                        className="text-sm"
                      >
                        取消
                      </Button>
                      <Button className="bg-orange-500 hover:bg-orange-600 text-sm">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        应用配置
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          )}
        </div>
      );
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center">
          <Link to="/data/synthesis/task">
            <Button type="text">
              <ArrowLeft className="w-4 h-4 mr-1" />
            </Button>
          </Link>
          <h1 className="text-xl font-bold bg-clip-text">创建合成任务</h1>
        </div>
        <Steps
          current={createStep - 1}
          size="small"
          items={[{ title: "基本信息" }, { title: "算子编排" }]}
          style={{ width: "50%", marginLeft: "auto" }}
        />
      </div>
      <div className="border-card flex-overflow-auto">
        {renderCreateTaskPage()}
        <div className="flex gap-2 justify-end p-4 border-top">
          <Button onClick={() => navigate("/data/synthesis/task")}>取消</Button>
          <Button
            type="primary"
            onClick={() => {
              form
                .validateFields()
                .then(() => setCreateStep(2))
                .catch(() => {});
            }}
            disabled={
              !form.getFieldValue("name") ||
              !form.getFieldValue("sourceDataset") ||
              selectedFiles.length === 0 ||
              !form.getFieldValue("targetCount")
            }
          >
            下一步
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </div>
    </div>
  );
}
