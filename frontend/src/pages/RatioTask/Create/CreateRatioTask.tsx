import { useState } from "react";
import { Button, Form, message } from "antd";
import { ArrowLeft, ChevronRight } from "lucide-react";
import { createRatioTaskUsingPost } from "@/pages/RatioTask/ratio.api.ts";
import type { Dataset } from "@/pages/DataManagement/dataset.model.ts";
import { useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import SelectDataset from "@/pages/RatioTask/Create/components/SelectDataset.tsx";
import BasicInformation from "@/pages/RatioTask/Create/components/BasicInformation.tsx";
import RatioConfig from "@/pages/RatioTask/Create/components/RatioConfig.tsx";
import {formatDate} from "@/utils/unit.ts";

export default function CreateRatioTask() {
  const navigate = useNavigate();
  const { t } = useTranslation();
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
        message.error(t("ratioTask.create.messages.configRequired"));
        return;
      }
      const totals = String(values.totalTargetCount);
      const config = ratioTaskForm.ratioConfigs.map((c) => {
        const dateRange = c.dateRange ? [formatDate(c.dateRange[0]), formatDate(c.dateRange[1])] : []
        return {
          datasetId: c.source,
          counts: String(c.quantity ?? 0),
          filterConditions: { label: c.labelFilter, dateRange: dateRange},
        };
      });

      setCreating(true);
      await createRatioTaskUsingPost({
        name: values.name,
        description: values.description,
        totals,
        config,
      });
      message.success(t("ratioTask.create.messages.createSuccess"));
      navigate("/data/synthesis/ratio-task");
    } catch {
      message.error(t("ratioTask.create.messages.createFailed"));
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
          <h1 className="text-xl font-bold bg-clip-text">{t("ratioTask.create.title")}</h1>
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
            {t("ratioTask.create.cancel")}
          </Button>
          <Button
            type="primary"
            onClick={handleCreateRatioTask}
            loading={creating}
            disabled={
              !ratioTaskForm.name || ratioTaskForm.ratioConfigs.length === 0
            }
          >
            {t("ratioTask.create.submit")}
          </Button>
        </div>
      </div>
    </div>
  );
}
