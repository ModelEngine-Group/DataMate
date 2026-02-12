import { useEffect, useState } from "react";
import type { Dataset, DatasetFile } from "@/pages/DataManagement/dataset.model";
import { DatasetType } from "@/pages/DataManagement/dataset.model";
import { Steps, Card, Select, Input, Button, Form, message, Tag, Tooltip, InputNumber } from "antd";
import { Eye, ArrowLeft, ArrowRight, Play, Search, Sparkles, Brain, Layers } from "lucide-react";
import { Link, useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [createStep, setCreateStep] = useState(1);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [selectedMap, setSelectedMap] = useState<Record<string, DatasetFile>>({});
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  // 当前选中的模板类型（QA / COT），用于高亮展示
  const [selectedSynthesisTypes, setSelectedSynthesisTypes] = useState<string[]>(["qa"]);
  const [taskType, setTaskType] = useState<"qa" | "cot">("qa");
  const [questionPrompt, setQuestionPrompt] = useState<string>("");
  const [answerPrompt, setAnswerPrompt] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [modelOptions, setModelOptions] = useState<{ label: string; value: string }[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [questionModelId, setQuestionModelId] = useState<string | undefined>(undefined);
  const [answerModelId, setAnswerModelId] = useState<string | undefined>(undefined);

  // 文本切片配置
  const [sliceConfig, setSliceConfig] = useState({
    processType: "DEFAULT_CHUNK" as
      | "DEFAULT_CHUNK"
      | "CHAPTER_CHUNK"
      | "PARAGRAPH_CHUNK"
      | "FIXED_LENGTH_CHUNK"
      | "CUSTOM_SEPARATOR_CHUNK",
    chunkSize: 3000,
    overlapSize: 100,
    delimiter: "",
  });

  // 问题/答案合成配置（与后端 question_synth_config / answer_synth_config 对齐）
  const [questionConfig, setQuestionConfig] = useState({
    number: 1,
    temperature: 0.7,
  });
  const [answerConfig, setAnswerConfig] = useState({
    // 答案侧不再需要 number，只保留温度
    temperature: 0.7,
  });
  // 合成总数上限，默认 5000
  const [maxQaPairs, setMaxQaPairs] = useState<number | undefined>(5000);

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

  // 问题 Prompt：固定使用 QUESTION 类型获取
  const fetchQuestionPrompt = async () => {
    try {
      const res = await getPromptByTypeUsingGet("QUESTION");
      const prompt = typeof res === "string" ? res : (res as { data?: string })?.data ?? "";
      setQuestionPrompt(prompt || "");
    } catch (e) {
      console.error(e);
      message.error(t('synthesisTask.create.messages.fetchQuestionPromptFailed'));
      setQuestionPrompt("");
    }
  };

  // 答案 Prompt：根据当前任务类型获取 QA/COT 模板
  const fetchAnswerPrompt = async (type: "qa" | "cot") => {
    try {
      const synthTypeParam = type === "qa" ? "QA" : "COT";
      const res = await getPromptByTypeUsingGet(synthTypeParam);
      const prompt = typeof res === "string" ? res : (res as { data?: string })?.data ?? "";
      setAnswerPrompt(prompt || "");
    } catch (e) {
      console.error(e);
      message.error(t('synthesisTask.create.messages.fetchAnswerPromptFailed'));
      setAnswerPrompt("");
    }
  };

  // 拉取模型列表，仅保留 CHAT 模型
  useEffect(() => {
    const loadModels = async () => {
      setModelsLoading(true);
      try {
        const { data } = await queryModelListUsingGet({ page: 0, size: 1000 });
        const chatModels: ModelI[] = (data?.content || []).filter(
          (model: ModelI) => model.type === "CHAT"
        );
        const options = chatModels.map((model) => ({
          label: `${model.modelName} (${model.provider})`,
          value: model.id,
        }));
        setModelOptions(options);
      } catch (error) {
        console.error(t('synthesisTask.create.messages.loadModelsFailed'), error);
      } finally {
        setModelsLoading(false);
      }
    };
    loadModels();
  }, []);

  // 默认选中第一个 CHAT 模型作为问题/答案模型
  useEffect(() => {
    if (modelOptions.length > 0) {
      setQuestionModelId((prev) => prev ?? modelOptions[0].value);
      setAnswerModelId((prev) => prev ?? modelOptions[0].value);
    }
  }, [modelOptions]);

  useEffect(() => {
    fetchDatasets();
  }, []);

  useEffect(() => {
    fetchQuestionPrompt();
    fetchAnswerPrompt(taskType);
  }, [taskType]);

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
      if (!(taskType === "qa" || taskType === "cot")) {
        message.error(t('synthesisTask.create.messages.selectType'));
        return;
      }
      if (!questionModelId || !answerModelId) {
        message.error(t('synthesisTask.create.messages.selectModels'));
        return;
      }
      if (selectedFiles.length === 0) {
        message.error(t('synthesisTask.create.messages.selectFiles'));
        return;
      }

      const synthConfig: Record<string, unknown> = {
        text_split_config: {
          chunk_size: sliceConfig.chunkSize,
          chunk_overlap: sliceConfig.overlapSize,
        },
        question_synth_config: {
          model_id: questionModelId,
          prompt_template: questionPrompt,
          number: questionConfig.number,
          temperature: questionConfig.temperature,
        },
        answer_synth_config: {
          model_id: answerModelId,
          prompt_template: answerPrompt,
          temperature: answerConfig.temperature,
        },
        max_qa_pairs: typeof maxQaPairs === "number" && maxQaPairs > 0 ? maxQaPairs : undefined,
      };

      const payload: Record<string, unknown> = {
        name: values.name || form.getFieldValue("name"),
        description: values.description ?? form.getFieldValue("description"),
        synthesis_type: taskType === "qa" ? "QA" : "COT",
        source_file_id: selectedFiles,
        synth_config: synthConfig,
      };

      // 清洗 description：空字符串转为 undefined，让后端用 validator 处理为 None
      const desc = payload.description;
      if (typeof desc === "string" && desc.trim().length === 0) {
        delete payload.description;
      }

      // 如果未设置 max_qa_pairs，则从 synth_config 中移除该字段，避免传递 undefined
      if (synthConfig.max_qa_pairs === undefined) {
        delete (synthConfig as { max_qa_pairs?: number }).max_qa_pairs;
      }

      setSubmitting(true);
      const res = (await createSynthesisTaskUsingPost(payload)) as CreateTaskApiResponse;

      const ok =
        res?.success === true ||
        res?.code === "0" ||
        res?.code === 0 ||
        typeof res?.data !== "undefined";

      if (ok) {
        message.success(t('synthesisTask.create.messages.createSuccess'));
        navigate("/data/synthesis/task");
      } else {
        message.error(res?.message || t('synthesisTask.create.messages.createFailed'));
      }
    } catch (error) {
      if (typeof error === "object" && error && "errorFields" in error) {
        message.error(t('synthesisTask.create.messages.fillRequired'));
        return;
      }
      console.error(error);
      message.error(error instanceof Error ? error.message : t('synthesisTask.create.messages.createFailed'));
    } finally {
      setSubmitting(false);
    }
  };

  // 仅两个一级类型，无二级目录 -> 扩展为模板配置
  const synthesisTemplates = [
    {
      id: "sft-qa",
      type: "qa" as const,
      title: t('synthesisTask.create.template.templates.sftQa.title'),
      subtitle: t('synthesisTask.create.template.templates.sftQa.subtitle'),
      badge: t('synthesisTask.create.template.templates.sftQa.badge'),
      description: t('synthesisTask.create.template.templates.sftQa.description'),
      colorClass: "from-sky-500/10 via-sky-400/5 to-transparent",
      borderClass: "border-sky-100 hover:border-sky-300",
      icon: Sparkles,
    },
    {
      id: "cot-reasoning",
      type: "cot" as const,
      title: t('synthesisTask.create.template.templates.cotReasoning.title'),
      subtitle: t('synthesisTask.create.template.templates.cotReasoning.subtitle'),
      badge: t('synthesisTask.create.template.templates.cotReasoning.badge'),
      description: t('synthesisTask.create.template.templates.cotReasoning.description'),
      colorClass: "from-violet-500/10 via-violet-400/5 to-transparent",
      borderClass: "border-violet-100 hover:border-violet-300",
      icon: Brain,
    },
  ];

  const handleTemplateClick = (tpl: (typeof synthesisTemplates)[number]) => {
    setTaskType(tpl.type);
    setSelectedSynthesisTypes([tpl.type]);
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
            <h2 className="font-medium text-gray-900 text-lg mb-2">{t('synthesisTask.create.step1')}</h2>
            <Form.Item label={t('synthesisTask.create.form.name')} name="name" rules={[{ required: true, message: t('synthesisTask.create.form.nameRequired') }]}>
              <Input placeholder={t('synthesisTask.create.form.namePlaceholder')} className="h-9 text-sm" />
            </Form.Item>
            <Form.Item label={t('synthesisTask.create.form.description')} name="description">
              <TextArea placeholder={t('synthesisTask.create.form.descriptionPlaceholder')} rows={3} className="resize-none text-sm" />
            </Form.Item>
            <DatasetFileTransfer open selectedFilesMap={selectedMap} onSelectedFilesChange={setSelectedMap} onDatasetSelect={(dataset) => {
              setSelectedDataset(dataset);
              form.setFieldsValue({ sourceDataset: dataset?.id ?? "" });
            }} datasetTypeFilter={DatasetType.TEXT} />
            {selectedDataset && (
              <div className="mt-4 p-3 bg-gray-50 rounded border text-xs text-gray-600">
                {t('synthesisTask.create.form.currentDataset', { name: selectedDataset.name, count: selectedFiles.length })}
              </div>
            )}
            <Form.Item hidden name="sourceDataset" rules={[{ required: true, message: t('synthesisTask.create.form.datasetRequired') }]}>
              <Input type="hidden" />
            </Form.Item>
          </Form>
        </div>
      );
    }

    if (createStep === 2) {
      return (
        <div className="px-1 pb-2 pt-1">
          <div className="grid grid-cols-12 gap-5 min-h-[520px]">
            {/* 左侧合成指令模板区：占 1/3 宽度 */}
            <div className="col-span-4 space-y-4">
              <Card className="shadow-sm border border-slate-100/80 bg-gradient-to-b from-slate-50/70 via-white to-white">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h1 className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-amber-500" />
                      {t('synthesisTask.create.template.title')}
                    </h1>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {t('synthesisTask.create.template.description')}
                    </p>
                  </div>
                  <Tag color="blue" className="text-[10px] px-2 py-0.5 rounded-full">
                    {t('synthesisTask.create.template.singleSelect')}
                  </Tag>
                </div>

                <div className="space-y-3">
                  <div className="relative">
                    <Search className="w-3 h-3 absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" />
                    <Input
                      placeholder={t('synthesisTask.create.template.searchPlaceholder')}
                      className="pl-6 text-[11px] h-7 rounded-full bg-slate-50/80 border-slate-100 focus:bg-white"
                      disabled
                    />
                  </div>

                  <div className="space-y-2 max-h-[420px] overflow-auto pr-1 custom-scrollbar-thin">
                    {synthesisTemplates.map((tpl) => {
                      const Icon = tpl.icon;
                      const active = selectedSynthesisTypes.includes(tpl.type);

                      return (
                        <div
                          key={tpl.id}
                          onClick={() => handleTemplateClick(tpl)}
                          className={`group relative rounded-xl border p-2.5 text-xs transition-all duration-200 cursor-pointer bg-white/80 hover:bg-white/100 ${
                            tpl.borderClass
                          } ${
                            active
                              ? "ring-1 ring-offset-1 ring-blue-500/60 border-blue-400/70 shadow-sm bg-gradient-to-r " +
                                tpl.colorClass
                              : "border-slate-100 hover:shadow-sm"
                          }`}
                        >
                          <div className="flex items-start gap-2.5">
                            <div
                              className={`mt-0.5 flex h-7 w-7 items-center justify-center rounded-full bg-white/60 shadow-sm border ${
                                active ? "border-blue-200" : "border-slate-100"
                              }`}
                            >
                              <Icon
                                className={`h-3.5 w-3.5 ${
                                  active
                                    ? "text-blue-500 drop-shadow-[0_0_6px_rgba(59,130,246,0.45)]"
                                    : "text-slate-400 group-hover:text-slate-500"
                                }`}
                              />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1.5 mb-0.5">
                                <span
                                  className={`truncate text-[12px] font-medium ${
                                    active ? "text-slate-900" : "text-slate-800"
                                  }`}
                                >
                                  {tpl.title}
                                </span>
                                {tpl.badge && (
                                  <Tag
                                    color={tpl.type === "qa" ? "processing" : "purple"}
                                    className="text-[10px] px-1.5 py-0 h-4 flex items-center rounded-full"
                                  >
                                    {tpl.badge}
                                  </Tag>
                                )}
                              </div>
                              <p className="text-[11px] text-slate-500 leading-snug truncate">
                                {tpl.subtitle}
                              </p>
                              <p className="mt-1 text-[11px] text-slate-400 leading-snug line-clamp-2">
                                {tpl.description}
                              </p>
                            </div>
                          </div>

                          <div className="absolute inset-y-2 right-1 flex items-center">
                            <Tooltip title={active ? "当前已选模板" : "点击应用此模板"}>
                              <div
                                className={`flex h-5 w-5 items-center justify-center rounded-full border text-[10px] transition-colors ${
                                  active
                                    ? "bg-blue-500 text-white border-blue-500 shadow-sm"
                                    : "bg-white/70 text-slate-300 border-slate-100 group-hover:text-slate-400"
                                }`}
                              >
                                {active ? "✓" : ""}
                              </div>
                            </Tooltip>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </Card>
            </div>

            {/* 右侧合成配置：占 2/3 宽度 */}
            <div className="col-span-8">
              <Card className="h-full shadow-sm border border-slate-100/80 bg-gradient-to-b from-white via-slate-50/60 to-white">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h1 className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
                      <Layers className="w-4 h-4 text-indigo-500" />
                      {t('synthesisTask.create.config.title')}
                    </h1>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {t('synthesisTask.create.config.description')}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Tooltip title="在正式创建任务前，先小批量运行验证效果">
                      <Button size="small" className="hover:bg-white text-[11px]" type="default">
                        <Eye className="w-3 h-3 mr-1" />
                        {t('synthesisTask.actions.enableDebug')}
                      </Button>
                    </Tooltip>
                  </div>
                </div>

                <div className="space-y-4">
                  {/* 步骤说明条 */}
                  <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-slate-50 border border-slate-100 text-[11px] text-slate-500">
                    <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-indigo-600 text-white text-[10px] font-semibold">1</span>
                    <span>{t('synthesisTask.create.config.steps.1')}</span>
                    <span className="text-slate-300">/</span>
                    <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-indigo-600 text-white text-[10px] font-semibold">2</span>
                    <span>{t('synthesisTask.create.config.steps.2')}</span>
                    <span className="text-slate-300">/</span>
                    <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-indigo-600 text-white text-[10px] font-semibold">3</span>
                    <span>{t('synthesisTask.create.config.steps.3')}</span>
                    <span className="text-slate-300">/</span>
                    <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-indigo-600 text-white text-[10px] font-semibold">4</span>
                    <span>{t('synthesisTask.create.config.steps.4')}</span>
                  </div>

                  {/* 1. 合成总数配置 */}
                  <div className="rounded-xl bg-white/90 border border-slate-100 px-4 py-3 shadow-[0_0_0_1px_rgba(148,163,184,0.12)]">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-indigo-600 text-white text-[10px] font-semibold">1</span>
                        <span className="text-[12px] font-medium text-slate-800">合成总数上限</span>
                      </div>
                      <span className="text-[10px] text-slate-400">控制整个任务最多生成的 QA 对数量</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <InputNumber
                        className="w-40"
                        min={1}
                        max={100000}
                        size="small"
                        value={maxQaPairs}
                        placeholder="不填则不限制"
                        onChange={(v) => setMaxQaPairs(typeof v === "number" ? v : undefined)}
                      />
                      <span className="text-[11px] text-slate-400">可选项，建议在大规模合成时设置上限</span>
                    </div>
                  </div>

                  {/* 2. 文本切片配置 */}
                  <div className="rounded-xl bg-white/90 border border-slate-100 px-4 py-3 shadow-[0_0_0_1px_rgba(148,163,184,0.12)]">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-indigo-600 text-white text-[10px] font-semibold">2</span>
                        <span className="text-[12px] font-medium text-slate-800">文本切片配置</span>
                      </div>
                      <span className="text-[10px] text-slate-400">影响上下文长度与召回粒度</span>
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                      <div>
                        <span className="text-[11px] font-medium text-gray-600">分块策略</span>
                        <Select
                          className="mt-1 w-full"
                          options={sliceOptions}
                          value={sliceConfig.processType}
                          onChange={(v) => setSliceConfig((p) => ({ ...p, processType: v }))}
                          size="small"
                        />
                      </div>
                      <div>
                        <span className="text-[11px] font-medium text-gray-600">分块大小</span>
                        <Input
                          className="mt-1"
                          type="number"
                          min={1}
                          value={sliceConfig.chunkSize}
                          onChange={(e) => setSliceConfig((p) => ({ ...p, chunkSize: Number(e.target.value) }))}
                          size="small"
                        />
                      </div>
                      <div>
                        <span className="text-[11px] font-medium text-gray-600">重叠大小</span>
                        <Input
                          className="mt-1"
                          type="number"
                          min={0}
                          value={sliceConfig.overlapSize}
                          onChange={(e) => setSliceConfig((p) => ({ ...p, overlapSize: Number(e.target.value) }))}
                          size="small"
                        />
                      </div>
                    </div>
                    {sliceConfig.processType === "CUSTOM_SEPARATOR_CHUNK" && (
                      <div className="mt-3">
                        <span className="text-[11px] font-medium text-gray-600">自定义分隔符</span>
                        <Input
                          className="mt-1"
                          placeholder={"例如：\\n\\n 或 ###"}
                          value={sliceConfig.delimiter}
                          onChange={(e) => setSliceConfig((p) => ({ ...p, delimiter: e.target.value }))}
                          size="small"
                        />
                      </div>
                    )}
                  </div>

                  {/* 3. 问题合成配置 */}
                  <div className="rounded-xl bg-white/90 border border-slate-100 px-4 py-3 shadow-[0_0_0_1px_rgba(148,163,184,0.12)]">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-indigo-600 text-white text-[10px] font-semibold">3</span>
                        <span className="text-[12px] font-medium text-slate-800">问题合成配置</span>
                      </div>
                      <span className="text-[10px] text-slate-400">控制每个 chunk 生成的问题数量与多样性</span>
                    </div>
                    <div className="grid grid-cols-12 gap-3 mb-3">
                      <div className="col-span-4">
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[11px] font-medium text-gray-600">问题生成数量</span>
                          <span className="text-[10px] text-slate-400">每千tokens生成的问题条数</span>
                        </div>
                        <InputNumber
                          className="mt-1 w-full"
                          min={1}
                          max={20}
                          size="small"
                          value={questionConfig.number}
                          onChange={(v) =>
                            setQuestionConfig((p) => ({ ...p, number: typeof v === "number" ? v : 1 }))
                          }
                        />
                      </div>
                      <div className="col-span-4">
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[11px] font-medium text-gray-600">温度 (Temperature)</span>
                          <span className="text-[10px] text-slate-400">数值越大，问题越发散、多样</span>
                        </div>
                        <InputNumber
                          className="mt-1 w-full"
                          min={0}
                          max={2}
                          step={0.1}
                          size="small"
                          value={questionConfig.temperature}
                          onChange={(v) =>
                            setQuestionConfig((p) => ({
                              ...p,
                              temperature: typeof v === "number" ? v : 0.7,
                            }))
                          }
                        />
                      </div>
                      <div className="col-span-4">
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[11px] font-medium text-gray-600">使用模型</span>
                          <span className="text-[10px] text-slate-400">用于生成问题的对话模型</span>
                        </div>
                        <Select
                          className="mt-1 w-full"
                          size="small"
                          options={modelOptions}
                          loading={modelsLoading}
                          value={questionModelId}
                          onChange={(v) => setQuestionModelId(v)}
                        />
                      </div>
                    </div>
                    <span className="text-[11px] font-medium text-gray-600">问题 Prompt 模板</span>
                    <p className="mt-0.5 text-[10px] text-slate-400">
                      用于指导模型如何从切片文本中生成高质量问题，可在保持变量占位符不变的前提下个性化修改。
                    </p>
                    <TextArea
                      value={questionPrompt}
                      onChange={(e) => setQuestionPrompt(e.target.value)}
                      rows={6}
                      className="mt-1 resize-none text-[11px] font-mono rounded-lg border-slate-200 bg-slate-50/60 hover:bg-slate-50 focus:bg-white"
                      placeholder={
                        taskType === "qa"
                          ? "将根据 SFT 问答合成场景预填问题生成 Prompt，可按需微调"
                          : "将根据 COT 推理合成场景预填问题生成 Prompt，可按需微调"
                      }
                    />
                  </div>

                  {/* 4. 答案合成配置 */}
                  <div className="rounded-xl bg-white/90 border border-slate-100 px-4 py-3 shadow-[0_0_0_1px_rgba(148,163,184,0.12)]">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-indigo-600 text-white text-[10px] font-semibold">4</span>
                        <span className="text-[12px] font-medium text-slate-800">答案合成配置</span>
                      </div>
                      <span className="text-[10px] text-slate-400">控制答案生成的稳定性与风格</span>
                    </div>
                    <div className="grid grid-cols-12 gap-3 mb-3">
                      <div className="col-span-4">
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[11px] font-medium text-gray-600">温度 (Temperature)</span>
                          <span className="text-[10px] text-slate-400">数值越小，答案越稳定、保守</span>
                        </div>
                        <InputNumber
                          className="mt-1 w-full"
                          min={0}
                          max={2}
                          step={0.1}
                          size="small"
                          value={answerConfig.temperature}
                          onChange={(v) =>
                            setAnswerConfig((p) => ({
                              ...p,
                              temperature: typeof v === "number" ? v : 0.7,
                            }))
                          }
                        />
                      </div>
                      <div className="col-span-4">
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[11px] font-medium text-gray-600">使用模型</span>
                          <span className="text-[10px] text-slate-400">用于生成答案的对话模型</span>
                        </div>
                        <Select
                          className="mt-1 w-full"
                          size="small"
                          options={modelOptions}
                          loading={modelsLoading}
                          value={answerModelId}
                          onChange={(v) => setAnswerModelId(v)}
                        />
                      </div>
                    </div>
                    <span className="text-[11px] font-medium text-gray-600">答案 Prompt 模板</span>
                    <p className="mt-0.5 text-[10px] text-slate-400">
                      用于约束模型回答的风格与内容范围，例如是否需要分步推理、是否必须引用原文关键信息等。
                    </p>
                    <TextArea
                      value={answerPrompt}
                      onChange={(e) => setAnswerPrompt(e.target.value)}
                      rows={6}
                      className="mt-1 resize-none text-[11px] font-mono rounded-lg border-slate-200 bg-slate-50/60 hover:bg-slate-50 focus:bg-white"
                      placeholder={
                        taskType === "qa"
                          ? "将根据 SFT 问答合成场景预填答案生成 Prompt，可按需微调"
                          : "将根据 COT 推理合成场景预填答案生成 Prompt，可按需微调"
                      }
                    />
                  </div>
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
          <h1 className="text-xl font-bold bg-clip-text">{t('synthesisTask.create.title')}</h1>
        </div>
        <Steps current={createStep - 1} size="small" items={[{ title: t('synthesisTask.create.step1') }, { title: t('synthesisTask.create.step2') }]} style={{ width: "50%", marginLeft: "auto" }} />
      </div>
      <div className="border-card flex-overflow-auto">
        {renderCreateTaskPage()}
        <div className="flex gap-2 justify-end p-4 border-top">
          {createStep === 1 ? (
            <>
              <Button onClick={() => navigate("/data/synthesis/task")}>{t('synthesisTask.actions.cancel')}</Button>
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
                {t('synthesisTask.actions.next')}
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </>
          ) : (
            <>
              <Button onClick={() => setCreateStep(1)} className="px-4 py-2 text-sm" type="default">
                <ArrowLeft className="w-4 h-4 mr-2" />
                {t('synthesisTask.actions.prev')}
              </Button>
              <Button
                onClick={handleCreateTask}
                disabled={
                  submitting ||
                  !form.getFieldValue("name") ||
                  !selectedDataset ||
                  selectedFiles.length === 0 ||
                  !questionModelId ||
                  !answerModelId
                }
                loading={submitting}
                className="px-6 py-2 text-sm font-semibold bg-purple-600 hover:bg-purple-700 shadow-lg"
                type="primary"
              >
                <Play className="w-4 h-4 mr-2" />
                {t('synthesisTask.actions.createTask')}
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
