import { useState } from "react";
import {
  Button,
  Card,
  Badge,
  Input,
  Select,
  Checkbox,
  Form,
  Typography,
} from "antd";
import {
  PlusOutlined,
  ArrowLeftOutlined,
  EditOutlined,
  SaveOutlined,
  DeleteOutlined,
} from "@ant-design/icons";
import {
  evaluationTemplates,
  presetEvaluationDimensions,
  sliceOperators,
} from "@/mock/evaluation";
import { useNavigate } from "react-router";

const { Title, Paragraph } = Typography;
const { Option } = Select;

const EvaluationTaskCreate = () => {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState([]);
  const [selectedTemplate, setSelectedTemplate] =
    useState<string>("dialogue_text");
  const [allDimensions, setAllDimensions] = useState<EvaluationDimension[]>([
    ...presetEvaluationDimensions,
  ]);
  const [editingDimension, setEditingDimension] = useState<string | null>(null);
  const [newDimension, setNewDimension] = useState({
    name: "",
    description: "",
  });
  const [createForm, setCreateForm] = useState({
    name: "",
    datasetId: "",
    evaluationType: "model" as "model" | "manual",
    dimensions: [] as string[],
    customDimensions: [] as EvaluationDimension[],
    sliceConfig: {
      threshold: 0.8,
      sampleCount: 100,
      method: "语义分割",
    },
    modelConfig: {
      url: "",
      apiKey: "",
      prompt: "",
      temperature: 0.3,
      maxTokens: 2000,
    },
  });

  const handleTemplateChange = (templateKey: string) => {
    setSelectedTemplate(templateKey);
    const template =
      evaluationTemplates[templateKey as keyof typeof evaluationTemplates];
    if (template) {
      const customDimensions = allDimensions.filter((d) => d.isCustom);
      setAllDimensions([...template.dimensions, ...customDimensions]);
    }
  };

  const handleAddCustomDimension = () => {
    if (newDimension.name.trim() && newDimension.description.trim()) {
      const customDimension: EvaluationDimension = {
        id: `custom_${Date.now()}`,
        name: newDimension.name.trim(),
        description: newDimension.description.trim(),
        category: "custom",
        isCustom: true,
        isEnabled: true,
      };
      setAllDimensions([...allDimensions, customDimension]);
      setNewDimension({ name: "", description: "" });
    }
  };

  const handleDimensionToggle = (id: string, checked: boolean) => {
    setAllDimensions(
      allDimensions.map((d) => (d.id === id ? { ...d, isEnabled: checked } : d))
    );
  };

  const handleEditDimension = (
    id: string,
    field: "name" | "description",
    value: string
  ) => {
    setAllDimensions(
      allDimensions.map((d) => (d.id === id ? { ...d, [field]: value } : d))
    );
  };

  const handleDeleteCustomDimension = (id: string) => {
    setAllDimensions(allDimensions.filter((d) => d.id !== id));
  };

  const handleDeletePresetDimension = (id: string) => {
    setAllDimensions(
      allDimensions.map((d) => (d.id === id ? { ...d, isEnabled: false } : d))
    );
  };

  const handleCreateTask = () => {
    const selectedDataset = datasets.find((d) => d.id === createForm.datasetId);
    if (!selectedDataset) return;

    const enabledDimensions = allDimensions.filter((d) => d.isEnabled);
    const presetDimensionIds = enabledDimensions
      .filter((d) => !d.isCustom)
      .map((d) => d.id);
    const customDimensions = enabledDimensions.filter((d) => d.isCustom);

    let finalPrompt = createForm.modelConfig.prompt;
    if (createForm.evaluationType === "model" && !finalPrompt.trim()) {
      finalPrompt = generateDefaultPrompt(selectedDataset.name);
    }

    const newTask: EvaluationTask = {
      id: Date.now().toString(),
      name: createForm.name,
      datasetId: createForm.datasetId,
      datasetName: selectedDataset.name,
      evaluationType: createForm.evaluationType,
      status: "pending",
      progress: 0,
      createdAt: new Date().toLocaleString(),
      description: `${
        createForm.evaluationType === "model" ? "模型自动" : "人工"
      }评估${selectedDataset.name}`,
      dimensions: presetDimensionIds,
      customDimensions: customDimensions,
      modelConfig:
        createForm.evaluationType === "model"
          ? {
              ...createForm.modelConfig,
              prompt: finalPrompt,
            }
          : undefined,
      metrics: {
        accuracy: 0,
        completeness: 0,
        consistency: 0,
        relevance: 0,
      },
      issues: [],
    };

    // 重置表单
    setCreateForm({
      name: "",
      datasetId: "",
      evaluationType: "model",
      dimensions: [],
      customDimensions: [],
      modelConfig: {
        url: "",
        apiKey: "",
        prompt: "",
        temperature: 0.3,
        maxTokens: 2000,
      },
    });
    navigate("/data/evaluation");
  };

  return (
    <div className="h-full">
      {/* 页面头部 */}
      <div className="flex items-center mb-2">
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate("/data/evaluation")}
        ></Button>
        <div className="text-xl font-bold">创建评估任务</div>
      </div>

      <Form layout="vertical">
        {/* 基本信息 */}
        <Card title="基本信息" style={{ marginBottom: 24 }}>
          <Form.Item label="任务名称" required>
            <Input
              value={createForm.name}
              onChange={(e) =>
                setCreateForm({ ...createForm, name: e.target.value })
              }
              placeholder="输入任务名称"
            />
          </Form.Item>
          <Form.Item label="选择数据集" required>
            <Select
              value={createForm.datasetId || undefined}
              onChange={(value) =>
                setCreateForm({ ...createForm, datasetId: value })
              }
              placeholder="选择要评估的数据集"
            >
              {datasets.map((dataset) => (
                <Option key={dataset.id} value={dataset.id}>
                  {dataset.name}（{dataset.fileCount} 文件 • {dataset.size}）
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item label="评估方式" required>
            <Select
              value={createForm.evaluationType}
              onChange={(value: "model" | "manual") =>
                setCreateForm({ ...createForm, evaluationType: value })
              }
            >
              <Option value="model">模型自动评估</Option>
              <Option value="manual">人工评估</Option>
            </Select>
          </Form.Item>
        </Card>

        {/* 算子配置 */}
        <Card title="切片算子配置" style={{ marginBottom: 24 }}>
          <Form.Item label="切片算子">
            <Select
              value={createForm.sliceConfig.method}
              onChange={(value) =>
                setCreateForm({
                  ...createForm,
                  sliceConfig: { ...createForm.sliceConfig, method: value },
                })
              }
              placeholder="选择切片算子"
            >
              {sliceOperators.map((operator) => (
                <Option key={operator.id} value={operator.name}>
                  {operator.name}{" "}
                  <Badge style={{ marginLeft: 8 }} count={operator.type} />
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item label="分隔符">
            <Input
              placeholder="输入分隔符，如 \\n\\n"
              value={createForm.sliceConfig.delimiter}
              onChange={(e) =>
                setCreateForm({
                  ...createForm,
                  sliceConfig: {
                    ...createForm.sliceConfig,
                    delimiter: e.target.value,
                  },
                })
              }
            />
          </Form.Item>
          <Form.Item label="分块大小">
            <Input
              type="number"
              value={createForm.sliceConfig.chunkSize}
              onChange={(e) =>
                setCreateForm({
                  ...createForm,
                  sliceConfig: {
                    ...createForm.sliceConfig,
                    chunkSize: Number(e.target.value),
                  },
                })
              }
            />
          </Form.Item>
          <Form.Item label="重叠长度">
            <Input
              type="number"
              value={createForm.sliceConfig.overlapLength}
              onChange={(e) =>
                setCreateForm({
                  ...createForm,
                  sliceConfig: {
                    ...createForm.sliceConfig,
                    overlapLength: Number(e.target.value),
                  },
                })
              }
            />
          </Form.Item>
          <Form.Item label="抽样比例">
            <Input
              type="number"
              value={createForm.sliceConfig.threshold}
              onChange={(e) =>
                setCreateForm({
                  ...createForm,
                  sliceConfig: {
                    ...createForm.sliceConfig,
                    threshold: Number(e.target.value),
                  },
                })
              }
            />
          </Form.Item>
        </Card>

        {/* 评估维度配置 */}
        <Card
          title={
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span>评估维度配置</span>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Select
                  value={selectedTemplate}
                  onChange={handleTemplateChange}
                  style={{ width: 160 }}
                >
                  {Object.entries(evaluationTemplates).map(
                    ([key, template]) => (
                      <Option key={key} value={key}>
                        {template.name}
                      </Option>
                    )
                  )}
                </Select>
                <Badge
                  count={allDimensions.filter((d) => d.isEnabled).length}
                  style={{ background: "#f0f0f0", color: "#333" }}
                />
              </div>
            </div>
          }
          style={{ marginBottom: 24 }}
        >
          {/* 维度表格 */}
          <div
            style={{
              border: "1px solid #f0f0f0",
              borderRadius: 6,
              marginBottom: 16,
            }}
          >
            <div
              style={{
                background: "#fafafa",
                padding: "8px 12px",
                borderBottom: "1px solid #f0f0f0",
                fontWeight: 500,
                fontSize: 13,
              }}
            >
              <div style={{ display: "flex", alignItems: "center" }}>
                <div style={{ width: 60 }}>启用</div>
                <div style={{ width: 160 }}>维度名称</div>
                <div style={{ flex: 1 }}>描述</div>
                <div style={{ width: 120 }}>操作</div>
              </div>
            </div>
            <div style={{ maxHeight: 320, overflowY: "auto" }}>
              {allDimensions.map((dimension) => (
                <div
                  key={dimension.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    padding: "8px 12px",
                    borderBottom: "1px solid #f5f5f5",
                  }}
                >
                  <div style={{ width: 60 }}>
                    <Checkbox
                      checked={dimension.isEnabled}
                      onChange={(e) =>
                        handleDimensionToggle(dimension.id, e.target.checked!)
                      }
                    />
                  </div>
                  <div style={{ width: 160 }}>
                    {editingDimension === dimension.id && dimension.isCustom ? (
                      <Input
                        value={dimension.name}
                        onChange={(e) =>
                          handleEditDimension(
                            dimension.id,
                            "name",
                            e.target.value
                          )
                        }
                        size="small"
                      />
                    ) : (
                      <span style={{ fontWeight: 500 }}>
                        {dimension.name}
                        {dimension.isCustom && (
                          <Badge
                            style={{
                              marginLeft: 4,
                              background: "#f9f0ff",
                              color: "#722ed1",
                            }}
                            count="自定义"
                          />
                        )}
                      </span>
                    )}
                  </div>
                  <div style={{ flex: 1 }}>
                    {editingDimension === dimension.id && dimension.isCustom ? (
                      <Input
                        value={dimension.description}
                        onChange={(e) =>
                          handleEditDimension(
                            dimension.id,
                            "description",
                            e.target.value
                          )
                        }
                        size="small"
                      />
                    ) : (
                      <span style={{ color: "#888" }}>
                        {dimension.description}
                      </span>
                    )}
                  </div>
                  <div style={{ width: 120 }}>
                    {editingDimension === dimension.id && dimension.isCustom ? (
                      <Button
                        type="text"
                        icon={<SaveOutlined />}
                        size="small"
                        onClick={() => setEditingDimension(null)}
                      />
                    ) : (
                      dimension.isCustom && (
                        <Button
                          type="text"
                          icon={<EditOutlined />}
                          size="small"
                          onClick={() => setEditingDimension(dimension.id)}
                        />
                      )
                    )}
                    <Button
                      type="text"
                      icon={<DeleteOutlined />}
                      size="small"
                      danger
                      onClick={() =>
                        dimension.isCustom
                          ? handleDeleteCustomDimension(dimension.id)
                          : handleDeletePresetDimension(dimension.id)
                      }
                      disabled={
                        allDimensions.filter((d) => d.isEnabled).length <= 1 &&
                        dimension.isEnabled
                      }
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
          {/* 添加自定义维度 */}
          <div style={{ background: "#fafafa", borderRadius: 6, padding: 16 }}>
            <div style={{ fontWeight: 500, marginBottom: 8 }}>
              添加自定义维度
            </div>
            <Input
              value={newDimension.name}
              onChange={(e) =>
                setNewDimension({ ...newDimension, name: e.target.value })
              }
              placeholder="维度名称"
              style={{ width: 180, marginRight: 8 }}
              size="small"
            />
            <Input
              value={newDimension.description}
              onChange={(e) =>
                setNewDimension({
                  ...newDimension,
                  description: e.target.value,
                })
              }
              placeholder="维度描述"
              style={{ width: 260, marginRight: 8 }}
              size="small"
            />
            <Button
              icon={<PlusOutlined />}
              onClick={handleAddCustomDimension}
              disabled={
                !newDimension.name.trim() || !newDimension.description.trim()
              }
              size="small"
            >
              添加维度
            </Button>
          </div>
        </Card>

        {/* 模型配置（仅在选择模型评估时显示） */}
        {createForm.evaluationType === "model" && (
          <Card title="模型配置" style={{ marginBottom: 24 }}>
            <Form.Item label="模型 URL" required>
              <Input
                value={createForm.modelConfig.url}
                onChange={(e) =>
                  setCreateForm({
                    ...createForm,
                    modelConfig: {
                      ...createForm.modelConfig,
                      url: e.target.value,
                    },
                  })
                }
                placeholder="https://api.openai.com/v1/chat/completions"
              />
            </Form.Item>
            <Form.Item label="API Key" required>
              <Input.Password
                value={createForm.modelConfig.apiKey}
                onChange={(e) =>
                  setCreateForm({
                    ...createForm,
                    modelConfig: {
                      ...createForm.modelConfig,
                      apiKey: e.target.value,
                    },
                  })
                }
                placeholder="sk-***"
              />
            </Form.Item>
          </Card>
        )}

        {/* 操作按钮 */}
        <Form.Item>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 12 }}>
            <Button onClick={() => navigate("/data/evaluation")}>取消</Button>
            <Button
              type="primary"
              onClick={handleCreateTask}
              disabled={
                !createForm.name ||
                !createForm.datasetId ||
                allDimensions.filter((d) => d.isEnabled).length === 0 ||
                (createForm.evaluationType === "model" &&
                  (!createForm.modelConfig.url ||
                    !createForm.modelConfig.apiKey))
              }
            >
              创建评估任务
            </Button>
          </div>
        </Form.Item>
      </Form>
    </div>
  );
};

export default EvaluationTaskCreate;
