import BasicInformation from "./components/BasicInformation";
import {
  queryDatasetByIdUsingGet,
  updateDatasetByIdUsingPut,
} from "../dataset.api";
import { useEffect, useState } from "react";
import { Dataset, DatasetType } from "../dataset.model";
import { App, Button, Form, Modal } from "antd";
import { useTranslation } from "react-i18next";

export default function EditDataset({
  open,
  data,
  onClose,
  onRefresh,
}: {
  open: boolean;
  data: Dataset | null;
  onClose: () => void;
  onRefresh?: (showMessage?: boolean) => void;
}) {
  const [form] = Form.useForm();
  const { message } = App.useApp();
  const { t } = useTranslation();

  const [newDataset, setNewDataset] = useState({
    name: "",
    description: "",
    datasetType: DatasetType.TEXT,
    tags: [],
  });
  const fetchDataset = async () => {
    if (!open) return;
    // 如果有id，说明是编辑模式
    if (data && data.id) {
      const { data: newData } = await queryDatasetByIdUsingGet(data.id);
      const updatedDataset = {
        ...newData,
        type: newData.type,
        tags: newData.tags.map((tag) => tag.name) || [],
      };
      setNewDataset(updatedDataset);
      form.setFieldsValue(updatedDataset);
    }
  };

  useEffect(() => {
    fetchDataset();
  }, [data]);

  const handleValuesChange = (_, allValues) => {
    setNewDataset({ ...newDataset, ...allValues });
  };

  const handleSubmit = async () => {
    const formValues = await form.validateFields();

    const params = {
      ...formValues,
      files: undefined,
    };
    try {
      await updateDatasetByIdUsingPut(data?.id, params);
      onClose();
      message.success(t("dataManagement.messages.updateSuccess"));
      onRefresh?.(false);
    } catch (error) {
      console.error(error);
      message.error(t("dataManagement.messages.updateFailed"));
      return;
    }
  };

  return (
    <Modal
      title={t("dataManagement.detail.editTitle", { name: data?.name || "" })}
      onCancel={onClose}
      open={open}
      width={600}
      maskClosable={false}
      footer={
        <>
          <Button onClick={onClose}>{t("dataManagement.actions.cancel")}</Button>
          <Button type="primary" onClick={handleSubmit}>
            {t("dataManagement.actions.confirm")}
          </Button>
        </>
      }
    >
      <Form
        form={form}
        initialValues={newDataset}
        onValuesChange={handleValuesChange}
        layout="vertical"
      >
        <BasicInformation
          data={newDataset}
          setData={setNewDataset}
          hidden={["datasetType"]}
        />
      </Form>
    </Modal>
  );
}
