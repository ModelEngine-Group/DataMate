import { useMemo, useState } from "react";
import { Button, Form, message } from "antd";
import { ArrowLeft, ChevronRight } from "lucide-react";
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
  const [distributions, setDistributions] = useState<
    Record<string, Record<string, number>>
  >({});

  const handleCreateRatioTask = async () => {
    try {
      const values = await form.validateFields();
      if (!ratioTaskForm.ratioConfigs.length) {
        message.error("请配置配比项");
        return;
      }
      const totals = String(values.totalTargetCount);
      const config = ratioTaskForm.ratioConfigs.map((c) => {
        return {
          datasetId: c.source,
          counts: String(c.quantity ?? 0),
          filterConditions: { label: c.labelFilter, dateRange: String(c.dateRange ?? 0)},
        };
      });

      setCreating(true);
      await createRatioTaskUsingPost({
        name: values.name,
        description: values.description,
        totals,
        config,
      });
      message.success("配比任务创建成功");
      navigate("/data/synthesis/ratio-task");
    } catch {
      message.error("配比任务创建失败，请重试");
    } finally {
      setCreating(false);
    }
  };

  const handleValuesChange = (_, allValues) => {
    setRatioTaskForm({ ...ratioTaskForm, ...allValues });
  };

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
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
      <div className="h-full flex-overflow-auto border-card">
        <div className="h-full overflow-auto p-6">
          <Form
            form={form}
            initialValues={ratioTaskForm}
            onValuesChange={handleValuesChange}
            layout="vertical"
            className="h-full"
          >
            <BasicInformation
              totalTargetCount={ratioTaskForm.totalTargetCount}
            />

            <div className="flex h-full">
              <SelectDataset
                selectedDatasets={ratioTaskForm.selectedDatasets}
                ratioType={ratioTaskForm.ratioType}
                onRatioTypeChange={(value) =>
                  setRatioTaskForm({
                    ...ratioTaskForm,
                    ratioType: value,
                    ratioConfigs: [],
                  })
                }
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
              <ChevronRight className="self-center" />
              <RatioConfig
                ratioType={ratioTaskForm.ratioType}
                selectedDatasets={ratioTaskForm.selectedDatasets}
                datasets={datasets}
                totalTargetCount={ratioTaskForm.totalTargetCount}
                distributions={distributions}
                onChange={(configs) =>
                  setRatioTaskForm((prev) => ({
                    ...prev,
                    ratioConfigs: configs,
                  }))
                }
              />
            </div>
          </Form>
        </div>
        <div className="flex justify-end gap-2 p-6">
          <Button onClick={() => navigate("/data/synthesis/ratio-task")}>
            取消
          </Button>
          <Button
            type="primary"
            onClick={handleCreateRatioTask}
            loading={creating}
            disabled={
              !ratioTaskForm.name || ratioTaskForm.ratioConfigs.length === 0
            }
          >
            创建
          </Button>
        </div>
      </div>
    </div>
  );
}
