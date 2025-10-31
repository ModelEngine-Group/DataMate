import { useState } from "react";
import { Button, Card, Form, Divider, message } from "antd";
import { ArrowLeft, Play, BarChart3, Shuffle, PieChart } from "lucide-react";
import { createRatioTaskUsingPost } from "@/pages/RatioTask/ratio.api.ts";
import type { Dataset } from "@/pages/DataManagement/dataset.model.ts";
import { useNavigate } from "react-router";
import SelectDataset from "@/pages/RatioTask/Create/components/SelectDataset.tsx";
import BasicInformation from "@/pages/RatioTask/Create/components/BasicInformation.tsx";
import RatioConfig from "@/pages/RatioTask/Create/components/RatioConfig.tsx";

export default function CreateRatioTask() {

  const navigate = useNavigate();
  const [form] = Form.useForm();
  // 配比任务相关状态
  const [ratioTaskForm, setRatioTaskForm] = useState({
    name: "",
    description: "",
    ratioType: "dataset" as "dataset" | "label",
    selectedDatasets: [] as string[],
    ratioConfigs: [] as any[],
    totalTargetCount: 10000,
    autoStart: true,
  });

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [creating, setCreating] = useState(false);
  const [distributions, setDistributions] = useState<Record<string, Record<string, number>>>({});


  const handleCreateRatioTask = async () => {
    try {
      const values = await form.validateFields();
      if (!ratioTaskForm.ratioConfigs.length) {
        message.error("请配置配比项");
        return;
      }
      // Build request payload
      const ratio_method = ratioTaskForm.ratioType === "dataset" ? "DATASET" : "TAG";
      const totals = String(values.totalTargetCount);
      const config = ratioTaskForm.ratioConfigs.map((c) => {
        if (ratio_method === "DATASET") {
          return {
            datasetId: String(c.source),
            counts: String(c.quantity ?? 0),
            filter_conditions: "",
          };
        }
        // TAG mode: source key like `${datasetId}_${label}`
        const source = String(c.source || "");
        const idx = source.indexOf("_");
        const datasetId = idx > 0 ? source.slice(0, idx) : source;
        const label = idx > 0 ? source.slice(idx + 1) : "";
        return {
          datasetId,
          counts: String(c.quantity ?? 0),
          filter_conditions: label ? JSON.stringify({ label }) : "",
        };
      });

      setCreating(true);
      await createRatioTaskUsingPost({
        name: values.name,
        description: values.description,
        totals,
        ratio_method,
        config,
      });
      message.success("配比任务创建成功");
      navigate("/data/synthesis/ratio-task");
    } catch {
      // 校验失败
    } finally {
      setCreating(false);
    }
  };

  // dataset selection is handled inside SelectDataset via onSelectedDatasetsChange

  const updateRatioConfig = (source: string, quantity: number) => {
    setRatioTaskForm((prev) => {
      const existingIndex = prev.ratioConfigs.findIndex(
        (config) => config.source === source
      );
      const totalOtherQuantity = prev.ratioConfigs
        .filter((config) => config.source !== source)
        .reduce((sum, config) => sum + config.quantity, 0);

      const newConfig = {
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

    const newConfigs = ratioTaskForm.selectedDatasets.map(
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

  // 标签模式下，更新某数据集的某个标签的数量
  const updateLabelRatioConfig = (datasetId: string, label: string, quantity: number) => {
    const sourceKey = `${datasetId}_${label}`;
    setRatioTaskForm((prev) => {
      const existingIndex = prev.ratioConfigs.findIndex((c) => c.source === sourceKey);
      const totalOtherQuantity = prev.ratioConfigs
        .filter((c) => c.source !== sourceKey)
        .reduce((sum, c) => sum + c.quantity, 0);

      const dist = distributions[datasetId] || {};
      const labelMax = dist[label] ?? Infinity;
      const cappedQuantity = Math.max(
        0,
        Math.min(quantity, prev.totalTargetCount - totalOtherQuantity, labelMax)
      );

      const newConfig = {
        id: sourceKey,
        name: label,
        type: "label",
        quantity: cappedQuantity,
        percentage: Math.round((cappedQuantity / prev.totalTargetCount) * 100),
        source: sourceKey,
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
            <SelectDataset
              selectedDatasets={ratioTaskForm.selectedDatasets}
              ratioType={ratioTaskForm.ratioType}
              onRatioTypeChange={(value) => setRatioTaskForm({ ...ratioTaskForm, ratioType: value, ratioConfigs: [] })}
              onSelectedDatasetsChange={(next) => {
                setRatioTaskForm((prev) => ({
                  ...prev,
                  selectedDatasets: next,
                  ratioConfigs: prev.ratioConfigs.filter((c) => {
                    const id = String(c.source);
                    // keep only items whose dataset id remains selected
                    const dsId = id.includes("_") ? id.split("_")[0] : id;
                    return next.includes(dsId);
                  }),
                }));
              }}
              onDistributionsChange={(next) => setDistributions(next)}
              onDatasetsChange={(list) => setDatasets(list)}
            />
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
                <BasicInformation totalTargetCount={ratioTaskForm.totalTargetCount} />
                <RatioConfig
                  ratioType={ratioTaskForm.ratioType}
                  selectedDatasets={ratioTaskForm.selectedDatasets}
                  datasets={datasets}
                  ratioConfigs={ratioTaskForm.ratioConfigs as any}
                  totalTargetCount={ratioTaskForm.totalTargetCount}
                  distributions={distributions}
                  onUpdateDatasetQuantity={(datasetId, quantity) => updateRatioConfig(datasetId, quantity)}
                  onUpdateLabelQuantity={(datasetId, label, quantity) => updateLabelRatioConfig(datasetId, label, quantity)}
                />
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
                      </div>
                    </div>
                  </div>
                )}
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
                    loading={creating}
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
