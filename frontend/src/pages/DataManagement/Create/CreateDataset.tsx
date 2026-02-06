import { useState } from "react";

import { ArrowLeft } from "lucide-react";
import { Button, Form, App } from "antd";
import { Link, useNavigate } from "react-router";
import { createDatasetUsingPost } from "../dataset.api";
import { DatasetType } from "../dataset.model";
import BasicInformation from "./components/BasicInformation";
import { useTranslation } from "react-i18next";

export default function DatasetCreate() {
  const navigate = useNavigate();
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const { t } = useTranslation();

  const [newDataset, setNewDataset] = useState({
    name: "",
    description: "",
    datasetType: DatasetType.TEXT,
    tags: [],
  });

  const handleSubmit = async () => {
    const formValues = await form.validateFields();

    const params = {
      ...formValues,
      files: undefined,
    };
    try {
      const { data } = await createDatasetUsingPost(params);
      message.success(t("dataManagement.messages.createSuccess"));
      navigate("/data/management/detail/" + data.id);
    } catch (error) {
      console.error(error);
      message.error(t("dataManagement.messages.createFailed"));
      return;
    }
  };

  const handleValuesChange = (_, allValues) => {
    setNewDataset({ ...newDataset, ...allValues });
  };

  return (
    <div className="h-full flex flex-col flex-1">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <Link to="/data/management">
            <Button type="text">
              <ArrowLeft className="w-4 h-4 mr-1" />
            </Button>
          </Link>
          <h1 className="text-xl font-bold bg-clip-text">
            {t("dataManagement.actions.createDataset")}
          </h1>
        </div>
      </div>

      {/* form */}
      <div className="flex-overflow-auto border-card">
        <div className="flex-1 p-6 overflow-auto">
          <Form
            form={form}
            initialValues={newDataset}
            onValuesChange={handleValuesChange}
            layout="vertical"
          >
            <BasicInformation data={newDataset} setData={setNewDataset} />
          </Form>
        </div>
        <div className="flex gap-2 justify-end p-6 border-top">
          <Button onClick={() => navigate("/data/management")}>
            {t("dataManagement.actions.cancel")}
          </Button>
          <Button
            type="primary"
            disabled={!newDataset.name || !newDataset.datasetType}
            onClick={handleSubmit}
          >
            {t("dataManagement.actions.confirm")}
          </Button>
        </div>
      </div>
    </div>
  );
}
