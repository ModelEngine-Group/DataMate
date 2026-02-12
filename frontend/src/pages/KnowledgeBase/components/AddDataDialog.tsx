import { useState } from "react";
import {
  Button,
  App,
  Input,
  Select,
  Form,
  Modal,
  Steps,
  Descriptions,
  Table,
} from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { addKnowledgeBaseFilesUsingPost } from "../knowledge-base.api";
import DatasetFileTransfer from "@/components/business/DatasetFileTransfer";
import { DescriptionsItemType } from "antd/es/descriptions";
import { getDatasetFileCols } from "../knowledge-base.const";
import { DatasetType } from "@/pages/DataManagement/dataset.model";
import { useTranslation } from "react-i18next";

export default function AddDataDialog({ knowledgeBase, onDataAdded }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const [currentStep, setCurrentStep] = useState(0);

  const [selectedFilesMap, setSelectedFilesMap] = useState({});

  // 定义分块选项
  const sliceOptions = [
    { label: t("knowledgeBase.const.sliceMethod.default"), value: "DEFAULT_CHUNK" },
    { label: t("knowledgeBase.const.sliceMethod.chapter"), value: "CHAPTER_CHUNK" },
    { label: t("knowledgeBase.const.sliceMethod.paragraph"), value: "PARAGRAPH_CHUNK" },
    { label: t("knowledgeBase.const.sliceMethod.fixedLength"), value: "FIXED_LENGTH_CHUNK" },
    { label: t("knowledgeBase.const.sliceMethod.customSeparator"), value: "CUSTOM_SEPARATOR_CHUNK" },
  ];

  // 定义初始状态
  const [newKB, setNewKB] = useState({
    processType: "DEFAULT_CHUNK",
    chunkSize: 500,
    overlapSize: 50,
    delimiter: "",
  });

  const steps = [
    {
      title: t("knowledgeBase.addData.steps.selectFiles.title"),
      description: t("knowledgeBase.addData.steps.selectFiles.description"),
    },
    {
      title: t("knowledgeBase.addData.steps.configParams.title"),
      description: t("knowledgeBase.addData.steps.configParams.description"),
    },
    {
      title: t("knowledgeBase.addData.steps.confirmUpload.title"),
      description: t("knowledgeBase.addData.steps.confirmUpload.description"),
    },
  ];

  // 获取已选择文件总数
  const getSelectedFilesCount = () => {
    return Object.values(selectedFilesMap).reduce(
      (total, ids) => total + ids.length,
      0
    );
  };

  const handleNext = () => {
    // 验证当前步骤
    if (currentStep === 0) {
      if (getSelectedFilesCount() === 0) {
        message.warning(t("knowledgeBase.addData.messages.selectOneFile"));
        return;
      }
    }
    if (currentStep === 1) {
      // 验证切片参数
      if (!newKB.processType) {
        message.warning(t("knowledgeBase.addData.messages.selectSliceMethod"));
        return;
      }
      if (!newKB.chunkSize || Number(newKB.chunkSize) <= 0) {
        message.warning(t("knowledgeBase.addData.messages.validChunkSize"));
        return;
      }
      if (!newKB.overlapSize || Number(newKB.overlapSize) < 0) {
        message.warning(t("knowledgeBase.addData.messages.validOverlapSize"));
        return;
      }
      if (newKB.processType === "CUSTOM_SEPARATOR_CHUNK" && !newKB.delimiter) {
        message.warning(t("knowledgeBase.addData.messages.inputDelimiter"));
        return;
      }
    }
    setCurrentStep(currentStep + 1);
  };

  const handlePrev = () => {
    setCurrentStep(currentStep - 1);
  };

  // 重置所有状态
  const handleReset = () => {
    setCurrentStep(0);
    setNewKB({
      processType: "DEFAULT_CHUNK",
      chunkSize: 500,
      overlapSize: 50,
      delimiter: "",
    });
    form.resetFields();
    setSelectedFilesMap({});
  };

  const handleAddData = async () => {
    if (getSelectedFilesCount() === 0) {
      message.warning(t("knowledgeBase.addData.messages.selectOneFile"));
      return;
    }

    try {
      // 构造符合API要求的请求数据
      const requestData = {
        files: Object.values(selectedFilesMap),
        processType: newKB.processType,
        chunkSize: Number(newKB.chunkSize), // 确保是数字类型
        overlapSize: Number(newKB.overlapSize), // 确保是数字类型
        delimiter: newKB.delimiter,
      };

      await addKnowledgeBaseFilesUsingPost(knowledgeBase.id, requestData);

      // 先通知父组件刷新数据（确保刷新发生在重置前）
      onDataAdded?.();

      message.success(t("knowledgeBase.addData.messages.addSuccess"));
      // 重置状态
      setOpen(false);
    } catch (error) {
      message.error(t("knowledgeBase.addData.messages.addFailed"));
      console.error("添加文件失败:", error);
    }
  };

  const handleModalCancel = () => {
    setOpen(false);
  };

  const descItems: DescriptionsItemType[] = [
    {
      label: t("knowledgeBase.addData.confirm.kbName"),
      key: "knowledgeBaseName",
      children: knowledgeBase?.name,
    },
    {
      label: t("knowledgeBase.addData.confirm.dataSource"),
      key: "dataSource",
      children: t("knowledgeBase.addData.confirm.dataset"),
    },
    {
      label: t("knowledgeBase.addData.confirm.totalFiles"),
      key: "totalFileCount",
      children: Object.keys(selectedFilesMap).length,
    },
    {
      label: t("knowledgeBase.addData.confirm.sliceMethod"),
      key: "chunkingMethod",
      children:
        sliceOptions.find((opt) => opt.value === newKB.processType)?.label ||
        "",
    },
    {
      label: t("knowledgeBase.addData.confirm.chunkSize"),
      key: "chunkSize",
      children: newKB.chunkSize,
    },
    {
      label: t("knowledgeBase.addData.confirm.overlapSize"),
      key: "overlapSize",
      children: newKB.overlapSize,
    },
    ...(newKB.processType === "CUSTOM_SEPARATOR_CHUNK" && newKB.delimiter
      ? [
          {
            label: t("knowledgeBase.addData.confirm.delimiter"),
            children: <span className="font-mono">{newKB.delimiter}</span>,
          },
        ]
      : []),
    {
      label: t("knowledgeBase.addData.confirm.fileList"),
      key: "fileList",
      span: 3,
      children: (
        <Table
          scroll={{ y: 400 }}
          rowKey="id"
          size="small"
          dataSource={Object.values(selectedFilesMap)}
          columns={getDatasetFileCols(t)}
        />
      ),
    },
  ];

  return (
    <>
      <Button
        type="primary"
        icon={<PlusOutlined />}
        onClick={() => {
          handleReset();
          setOpen(true);
        }}
      >
        {t("knowledgeBase.addData.title")}
      </Button>
      <Modal
        title={t("knowledgeBase.addData.title")}
        open={open}
        onCancel={handleModalCancel}
        footer={
          <div className="space-x-2">
            {currentStep === 0 && (
              <Button onClick={handleModalCancel}>{t("knowledgeBase.addData.confirm.cancel")}</Button>
            )}
            {currentStep > 0 && (
              <Button disabled={false} onClick={handlePrev}>
                {t("knowledgeBase.addData.confirm.previous")}
              </Button>
            )}
            {currentStep < steps.length - 1 ? (
              <Button
                type="primary"
                disabled={
                  Object.keys(selectedFilesMap).length === 0 ||
                  !newKB.chunkSize ||
                  !newKB.overlapSize ||
                  !newKB.processType
                }
                onClick={handleNext}
              >
                {t("knowledgeBase.addData.confirm.next")}
              </Button>
            ) : (
              <Button type="primary" onClick={handleAddData}>
                {t("knowledgeBase.addData.confirmUpload")}
              </Button>
            )}
          </div>
        }
        width={1000}
      >
        <div>
          {/* 步骤导航 */}
          <Steps
            current={currentStep}
            size="small"
            items={steps}
            labelPlacement="vertical"
          />

          {/* 步骤内容 */}
          {currentStep === 0 && (
            <DatasetFileTransfer
              open={open}
              selectedFilesMap={selectedFilesMap}
              onSelectedFilesChange={setSelectedFilesMap}
              datasetTypeFilter={DatasetType.TEXT}
            />
          )}

          <Form
            hidden={currentStep !== 1}
            form={form}
            layout="vertical"
            initialValues={newKB}
            onValuesChange={(_, allValues) => setNewKB(allValues)}
          >
            <div className="space-y-6">
              <Form.Item
                label={t("knowledgeBase.addData.form.sliceMethodLabel")}
                name="processType"
                required
                rules={[{ required: true }]}
              >
                <Select options={sliceOptions} />
              </Form.Item>

              <div className="grid grid-cols-2 gap-6">
                <Form.Item
                  label={t("knowledgeBase.addData.form.chunkSizeLabel")}
                  name="chunkSize"
                  rules={[
                    {
                      required: true,
                      message: t("knowledgeBase.addData.messages.validChunkSize"),
                    },
                  ]}
                >
                  <Input type="number" placeholder={t("knowledgeBase.addData.form.chunkSizePlaceholder")} />
                </Form.Item>
                <Form.Item
                  label={t("knowledgeBase.addData.form.overlapLabel")}
                  name="overlapSize"
                  rules={[
                    {
                      required: true,
                      message: t("knowledgeBase.addData.messages.validOverlapSize"),
                    },
                  ]}
                >
                  <Input type="number" placeholder={t("knowledgeBase.addData.form.overlapPlaceholder")} />
                </Form.Item>
              </div>

              {newKB.processType === "CUSTOM_SEPARATOR_CHUNK" && (
                <Form.Item
                  label={t("knowledgeBase.addData.form.delimiterLabel")}
                  name="delimiter"
                  rules={[
                    {
                      required: true,
                      message: t("knowledgeBase.addData.messages.inputDelimiter"),
                    },
                  ]}
                >
                  <Input placeholder={t("knowledgeBase.addData.form.delimiterPlaceholder")} />
                </Form.Item>
              )}
            </div>
          </Form>

          <div className="space-y-6" hidden={currentStep !== 2}>
            <div className="">
              <div className="text-lg font-medium mb-3">{t("knowledgeBase.addData.confirm.uploadConfirmTitle")}</div>
              <Descriptions layout="vertical" size="small" items={descItems} />
            </div>
            <div className="text-sm text-yellow-600">
              {t("knowledgeBase.addData.confirm.uploadHint")}
            </div>
          </div>
        </div>
      </Modal>
    </>
  );
}
