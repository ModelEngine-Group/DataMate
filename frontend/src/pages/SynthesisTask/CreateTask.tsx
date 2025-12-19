import { useEffect, useState } from "react";
import type { Dataset, DatasetFile } from "@/pages/DataManagement/dataset.model";
import { Steps, Card, Select, Input, Checkbox, Button, Form, message } from "antd";
import { Eye, ArrowLeft, ArrowRight, Play, Search, MoreHorizontal } from "lucide-react";
import { Link, useNavigate } from "react-router";
import { queryDatasetsUsingGet } from "../DataManagement/dataset.api";
import DatasetFileTransfer from "@/components/business/DatasetFileTransfer";
import { createSynthesisTaskUsingPost, getPromptByTypeUsingGet } from "./synthesis-api";
import { queryModelListUsingGet } from "@/pages/SettingsPage/settings.apis";
import type { ModelI } from "@/pages/SettingsPage/ModelAccess";

const { TextArea } = Input;

interface CreateTaskFormValues {
  name: string;
  sourceDataset: string;
  description?: string;
}

interface CreateTaskApiResponse {
  code?: string | number;
  message?: string;
  data?: unknown;
  success?: boolean;
}

export default function SynthesisTaskCreate() {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [createStep, setCreateStep] = useState(1);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [selectedMap, setSelectedMap] = useState<Record<string, DatasetFile>>({});
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [selectedSynthesisTypes, setSelectedSynthesisTypes] = useState<string[]>(["qa"]);
  const [taskType, setTaskType] = useState<"qa" | "cot">("qa");
  const [promptTemplate, setPromptTemplate] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [modelOptions, setModelOptions] = useState<{ label: string; value: string }[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState<string | undefined>(undefined);
  const [sliceConfig, setSliceConfig] = useState({
    processType: "DEFAULT_CHUNK" as
      | "DEFAULT_CHUNK"
      | "CHAPTER_CHUNK"
      | "PARAGRAPH_CHUNK"
      | "FIXED_LENGTH_CHUNK"
      | "CUSTOM_SEPARATOR_CHUNK",
    chunkSize: 500,
    overlapSize: 50,
    delimiter: "",
  });
  const sliceOptions = [
    { label: "默认分块", value: "DEFAULT_CHUNK" },
    { label: "按章节分块", value: "CHAPTER_CHUNK" },
    { label: "按段落分块", value: "PARAGRAPH_CHUNK" },
    { label: "固定长度分块", value: "FIXED_LENGTH_CHUNK" },
    { label: "自定义分隔符分块", value: "CUSTOM_SEPARATOR_CHUNK" },
  ];

  const fetchDatasets = async () => {
    const { data } = await queryDatasetsUsingGet({ page: 1, size: 1000 });
    return data;
  };

  const fetchPrompt = async (type: "qa" | "cot") => {
    try {
      const synthTypeParam = type.toUpperCase();
      const res = await getPromptByTypeUsingGet(synthTypeParam);
      const prompt = typeof res === "string" ? res : (res as { data?: string })?.data ?? "";
      setPromptTemplate(prompt || "");
    } catch (e) {
      console.error(e);
      message.error("获取提示词模板失败");
      setPromptTemplate("");
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  useEffect(() => {
    fetchPrompt(taskType);
  }, [taskType]);

  useEffect(() => {
    const loadModels = async () => {
      setModelsLoading(true);
      try {
        const { data } = await queryModelListUsingGet({ page: 0, size: 1000 });
        const options = (data?.content || []).map((model: ModelI) => ({
          label: `${model.modelName} (${model.provider})`,
          value: model.id,
        }));
        setModelOptions(options);
      } catch (error) {
        console.error("加载模型列表失败", error);
      } finally {
        setModelsLoading(false);
      }
    };
    loadModels();
  }, []);

  useEffect(() => {
    if (!selectedModel && modelOptions.length > 0) {
      setSelectedModel(modelOptions[0].value);
    }
  }, [modelOptions, selectedModel]);

  // 表单数据
  const [formValues, setFormValues] = useState<CreateTaskFormValues>({
    name: "",
    sourceDataset: "",
    description: "",
  });

  const handleValuesChange: NonNullable<Parameters<typeof Form>[0]["onValuesChange"]> = (
    _changed,
    allValues
  ) => {
    setFormValues(allValues as CreateTaskFormValues);
  };

  // 当选择文件变化时，同步 selectedFiles 为 ID 列表
  useEffect(() => {
    const ids = Object.values(selectedMap).map((f) => String(f.id));
    setSelectedFiles(ids);
  }, [selectedMap]);

  const handleCreateTask = async () => {
    try {
      const values = (await form.validateFields()) as CreateTaskFormValues;
      // precise validation
      if (!(taskType === "qa" || taskType === "cot")) {
        message.error("请选择一个合成类型");
        return;
      }
      if (!selectedModel) {
        message.error("请选择模型");
        return;
      }
      if (selectedFiles.length === 0) {
        message.error("请至少选择一个文件");
        return;
      }

      // 构造后端要求的参数格式
      const payload: Record<string, unknown> = {
        name: values.name || form.getFieldValue("name"),
        model_id: selectedModel,
        source_file_id: selectedFiles,
        text_split_config: {
          chunk_size: sliceConfig.chunkSize,
          chunk_overlap: sliceConfig.overlapSize,
        },
        synthesis_config: {
          prompt_template: promptTemplate,
        },
        synthesis_type: taskType === "qa" ? "QA" : "COT",
      };

      // 只有在有真实内容时携带 description，避免强制传空字符串
      const desc = values.description ?? form.getFieldValue("description");
      if (typeof desc === "string" && desc.trim().length > 0) {
        payload.description = desc.trim();
      }

      setSubmitting(true);
      const res = (await createSynthesisTaskUsingPost(payload)) as CreateTaskApiResponse;

      const ok =
        res?.success === true ||
        res?.code === "0" ||
        res?.code === 0 ||
        typeof res?.data !== "undefined";

      if (ok) {
        message.success("合成任务创建成功");
        navigate("/data/synthesis/task");
      } else {
        message.error(res?.message || "合成任务创建失败");
      }
    } catch (error) {
      if (typeof error === "object" && error && "errorFields" in error) {
        message.error("请填写所有必填项");
        return;
      }
      console.error(error);
      message.error((error instanceof Error ? error.message : "合成任务创建失败"));
    } finally {
      setSubmitting(false);
    }
  };

  // 仅两个一级类型，无二级目录
  const synthesisTypes = [
    { id: "qa", name: "生成问答对" },
    { id: "cot", name: "生成COT链式推理" },
  ] as const;

  const handleSynthesisTypeSelect = (typeId: "qa" | "cot") => {
    setSelectedSynthesisTypes((prev) => {
      const next = prev.includes(typeId) ? [] : [typeId];
      if (next[0] === "qa") setTaskType("qa");
      if (next[0] === "cot") setTaskType("cot");
      return next;
    });
  };

  useEffect(() => {
    // 进入第二步时，若未选择类型，默认选择 QA，避免误报
    if (createStep === 2 && !(taskType === "qa" || taskType === "cot")) {
      setTaskType("qa");
      setSelectedSynthesisTypes(["qa"]);
    }
  }, [createStep, taskType]);

  const renderCreateTaskPage = () => {
    if (createStep === 1) {
      return (
        <div className="flex-1 p-4 overflow-auto">
          <Form form={form} layout="vertical" initialValues={formValues} onValuesChange={handleValuesChange} autoComplete="off">
            <h2 className="font-medium text-gray-900 text-lg mb-2">基本信息</h2>
            <Form.Item label="任务名称" name="name" rules={[{ required: true, message: "请输入任务名称" }]}>
              <Input placeholder="输入任务名称" className="h-9 text-sm" />
            </Form.Item>
            <Form.Item label="任务描述" name="description">
              <TextArea placeholder="描述任务的目的和要求（可选）" rows={3} className="resize-none text-sm" />
            </Form.Item>
            <DatasetFileTransfer open selectedFilesMap={selectedMap} onSelectedFilesChange={setSelectedMap} onDatasetSelect={(dataset) => {
              setSelectedDataset(dataset);
              form.setFieldsValue({ sourceDataset: dataset?.id ?? "" });
            }} />
            {selectedDataset && (
              <div className="mt-4 p-3 bg-gray-50 rounded border text-xs text-gray-600">
                当前数据集：<span className="font-medium text-gray-900">{selectedDataset.name}</span>
              </div>
            )}
            <Form.Item hidden name="sourceDataset" rules={[{ required: true, message: "请选择数据集" }]}>
              <Input type="hidden" />
            </Form.Item>
          </Form>
        </div>
      );
    }

    if (createStep === 2) {
      return (
        <div className="">
          <div className="grid grid-cols-12 gap-6 min-h-[500px]">
            {/* 左侧合成指令（仅两个一级类型，单选） */}
            <div className="col-span-4 space-y-4">
              <Card className="shadow-sm border-0 bg-white">
                <h1 className="text-base">合成指令（仅支持单选）</h1>
                <div className="space-y-3 mb-4">
                  <div className="relative">
                    <Search className="w-3 h-3 absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <Input placeholder="搜索名称" className="pl-7 text-xs h-8" />
                  </div>
                </div>
                <div className="space-y-2">
                  {synthesisTypes.map((type) => (
                    <div
                      key={type.id}
                      className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer text-xs transition-colors ${
                        selectedSynthesisTypes.includes(type.id)
                          ? "bg-blue-50 text-blue-700 border border-blue-200"
                          : "hover:bg-gray-50"
                      }`}
                      onClick={() => handleSynthesisTypeSelect(type.id)}
                    >
                      <Checkbox
                        checked={selectedSynthesisTypes.includes(type.id)}
                        onChange={() => handleSynthesisTypeSelect(type.id)}
                      />
                      <span className="flex-1">{type.name}</span>
                      <MoreHorizontal className="w-3 h-3 text-gray-400" />
                    </div>
                  ))}
                </div>
              </Card>
            </div>

            {/* 右侧合成配置 */}
            <div className="col-span-8">
              <Card className="h-full shadow-sm border-0 bg-white">
                <div className="flex items-center justify-between">
                  <h1>合成配置</h1>
                  <div className="flex items-center gap-2">
                    <Button className="hover:bg-white text-xs" type="default">
                      <Eye className="w-3 h-3 mr-1" />
                      启用调测
                    </Button>
                  </div>
                </div>

                <div className="space-y-4">
                  {/* 切片配置 */}
                  <Card className="shadow-sm border">
                    <div className="grid grid-cols-3 gap-3">
                      <div>
                        <span className="text-xs font-medium text-gray-600">分块策略</span>
                        <Select
                          options={sliceOptions}
                          value={sliceConfig.processType}
                          onChange={(v) => setSliceConfig((p) => ({ ...p, processType: v }))}
                        />
                      </div>
                      <div>
                        <span className="text-xs font-medium text-gray-600">分块大小</span>
                        <Input
                          type="number"
                          min={1}
                          value={sliceConfig.chunkSize}
                          onChange={(e) => setSliceConfig((p) => ({ ...p, chunkSize: Number(e.target.value) }))}
                        />
                      </div>
                      <div>
                        <span className="text-xs font-medium text-gray-600">重叠大小</span>
                        <Input
                          type="number"
                          min={0}
                          value={sliceConfig.overlapSize}
                          onChange={(e) => setSliceConfig((p) => ({ ...p, overlapSize: Number(e.target.value) }))}
                        />
                      </div>
                    </div>
                    {sliceConfig.processType === "CUSTOM_SEPARATOR_CHUNK" && (
                      <div className="mt-3">
                        <span className="text-xs font-medium text-gray-600">自定义分隔符</span>
                        <Input
                          placeholder={"例如：\\n\\n 或 ###"}
                          value={sliceConfig.delimiter}
                          onChange={(e) => setSliceConfig((p) => ({ ...p, delimiter: e.target.value }))}
                        />
                      </div>
                    )}
                  </Card>

                  {/* 模型选择 */}
                  <Card className="shadow-sm border">
                    <span className="text-xs font-medium text-gray-600">模型选择</span>
                    <Select
                      placeholder="选择模型"
                      options={modelOptions}
                      loading={modelsLoading}
                      value={selectedModel}
                      onChange={(value) => setSelectedModel(value)}
                    />
                  </Card>

                  {/* Prompt 配置 */}
                  <Card className="shadow-sm border">
                    <span className="text-xs font-medium text-gray-600">Prompt 配置</span>
                    <TextArea
                      value={promptTemplate}
                      onChange={(e) => setPromptTemplate(e.target.value)}
                      rows={8}
                      className="resize-none text-xs font-mono"
                      placeholder={taskType === "qa" ? "正在加载 QA 提示词模板..." : "正在加载 COT 提示词模板..."}
                    />
                  </Card>
                </div>

                {/* 页面底部统一操作条渲染，不在此处放置按钮 */}
              </Card>
            </div>
          </div>
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
        <Steps current={createStep - 1} size="small" items={[{ title: "基本信息" }, { title: "算子编排" }]} style={{ width: "50%", marginLeft: "auto" }} />
      </div>
      <div className="border-card flex-overflow-auto">
        {renderCreateTaskPage()}
        <div className="flex gap-2 justify-end p-4 border-top">
          {createStep === 1 ? (
            <>
              <Button onClick={() => navigate("/data/synthesis/task")}>取消</Button>
              <Button
                type="primary"
                onClick={() => {
                  form
                    .validateFields()
                    .then(() => setCreateStep(2))
                    .catch(() => {});
                }}
                disabled={!form.getFieldValue("name") || !selectedDataset || selectedFiles.length === 0}
              >
                下一步
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </>
          ) : (
            <>
              <Button onClick={() => setCreateStep(1)} className="px-4 py-2 text-sm" type="default">
                <ArrowLeft className="w-4 h-4 mr-2" />
                上一步
              </Button>
              <Button
                onClick={handleCreateTask}
                disabled={
                  submitting ||
                  !form.getFieldValue("name") ||
                  !selectedDataset ||
                  selectedFiles.length === 0 ||
                  !selectedModel
                }
                loading={submitting}
                className="px-6 py-2 text-sm font-semibold bg-purple-600 hover:bg-purple-700 shadow-lg"
                type="primary"
              >
                <Play className="w-4 h-4 mr-2" />
                创建任务
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
