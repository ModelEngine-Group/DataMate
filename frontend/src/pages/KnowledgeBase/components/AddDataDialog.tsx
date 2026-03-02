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

const IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "tiff", "tif"];
const VIDEO_EXTENSIONS = ["mp4", "avi", "mov", "mkv", "wmv", "flv", "webm", "m4v", "3gp"];

export default function AddDataDialog({ knowledgeBase, onDataAdded }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedFilesMap, setSelectedFilesMap] = useState({});

  const isImageFile = (fileName) => {
    const ext = fileName?.split(".").pop()?.toLowerCase();
    return IMAGE_EXTENSIONS.includes(ext);
  };

  const isVideoFile = (fileName) => {
    const ext = fileName?.split(".").pop()?.toLowerCase();
    return VIDEO_EXTENSIONS.includes(ext);
  };

  const isMediaFile = (fileName) => {
    return isImageFile(fileName) || isVideoFile(fileName);
  };

  const isAllMediaFiles = () => {
    const files = Object.values(selectedFilesMap);
    if (files.length === 0) return false;
    return files.every((file) => {
      const ext = file.fileName?.split(".").pop()?.toLowerCase();
      return IMAGE_EXTENSIONS.includes(ext) || VIDEO_EXTENSIONS.includes(ext);
    });
  };

  const getMediaType = () => {
    const files = Object.values(selectedFilesMap);
    if (files.length === 0) return null;
    const hasImage = files.some((file) => isImageFile(file.fileName));
    const hasVideo = files.some((file) => isVideoFile(file.fileName));
    if (hasImage && hasVideo) return "mixed";
    if (hasVideo) return "video";
    if (hasImage) return "image";
    return null;
  };

  const sliceOptions = [
    { label: t("knowledgeBase.const.sliceMethod.default"), value: "DEFAULT_CHUNK" },
    { label: t("knowledgeBase.const.sliceMethod.chapter"), value: "CHAPTER_CHUNK" },
    { label: t("knowledgeBase.const.sliceMethod.paragraph"), value: "PARAGRAPH_CHUNK" },
    { label: t("knowledgeBase.const.sliceMethod.fixedLength"), value: "FIXED_LENGTH_CHUNK" },
    { label: t("knowledgeBase.const.sliceMethod.customSeparator"), value: "CUSTOM_SEPARATOR_CHUNK" },
  ];

  const [newKB, setNewKB] = useState({
    processType: "DEFAULT_CHUNK",
    chunkSize: 500,
    overlapSize: 50,
    delimiter: "",
  });

  const steps = isAllMediaFiles()
    ? [
        {
          title: t("knowledgeBase.addData.steps.selectFiles.title"),
          description: t("knowledgeBase.addData.steps.selectFiles.description"),
        },
        {
          title: t("knowledgeBase.addData.steps.confirmUpload.title"),
          description: t("knowledgeBase.addData.steps.confirmUpload.description"),
        },
      ]
    : [
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

  const getSelectedFilesCount = () => {
    return Object.values(selectedFilesMap).length;
  };

  const handleNext = () => {
    if (currentStep === 0) {
      if (getSelectedFilesCount() === 0) {
        message.warning(t("knowledgeBase.addData.messages.selectOneFile"));
        return;
      }
      if (isAllMediaFiles()) {
        setCurrentStep(1);
        return;
      }
    }
    if (currentStep === 1) {
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
    if (currentStep === 1 && isAllMediaFiles()) {
      setCurrentStep(0);
      return;
    }
    setCurrentStep(currentStep - 1);
  };

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
      const requestData = {
        files: Object.values(selectedFilesMap),
        processType: newKB.processType,
        chunkSize: Number(newKB.chunkSize),
        overlapSize: Number(newKB.overlapSize),
        delimiter: newKB.delimiter,
      };

      await addKnowledgeBaseFilesUsingPost(knowledgeBase.id, requestData);
      onDataAdded?.();
      message.success(t("knowledgeBase.addData.messages.addSuccess"));
      setOpen(false);
    } catch (error) {
      message.error(t("knowledgeBase.addData.messages.addFailed"));
      console.error("添加文件失败:", error);
    }
  };

  const handleModalCancel = () => {
    setOpen(false);
  };

  const getMediaDescItems = (): DescriptionsItemType[] => {
    const mediaType = getMediaType();
    let fileTypeLabel = t("knowledgeBase.addData.confirm.mediaFiles");
    if (mediaType === "image") {
      fileTypeLabel = t("knowledgeBase.addData.confirm.imageFiles");
    } else if (mediaType === "video") {
      fileTypeLabel = t("knowledgeBase.addData.confirm.videoFiles");
    }
    
    return [
      { label: t("knowledgeBase.addData.confirm.kbName"), key: "kbName", children: knowledgeBase?.name },
      { label: t("knowledgeBase.addData.confirm.dataSource"), key: "dataSource", children: t("knowledgeBase.addData.confirm.dataset") },
      { label: t("knowledgeBase.addData.confirm.totalFiles"), key: "totalFiles", children: getSelectedFilesCount() },
      { label: t("knowledgeBase.addData.confirm.fileType"), key: "fileType", children: fileTypeLabel },
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
  };

  const getTextDescItems = (): DescriptionsItemType[] => [
    { label: t("knowledgeBase.addData.confirm.kbName"), key: "kbName", children: knowledgeBase?.name },
    { label: t("knowledgeBase.addData.confirm.dataSource"), key: "dataSource", children: t("knowledgeBase.addData.confirm.dataset") },
    { label: t("knowledgeBase.addData.confirm.totalFiles"), key: "totalFiles", children: getSelectedFilesCount() },
    { label: t("knowledgeBase.addData.confirm.sliceMethod"), key: "sliceMethod", children: sliceOptions.find((opt) => opt.value === newKB.processType)?.label || "" },
    { label: t("knowledgeBase.addData.confirm.chunkSize"), key: "chunkSize", children: newKB.chunkSize },
    { label: t("knowledgeBase.addData.confirm.overlapSize"), key: "overlapSize", children: newKB.overlapSize },
    ...(newKB.processType === "CUSTOM_SEPARATOR_CHUNK" && newKB.delimiter
      ? [{ label: t("knowledgeBase.addData.confirm.delimiter"), children: <span className="font-mono">{newKB.delimiter}</span> }]
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

  const descItems = isAllMediaFiles() ? getMediaDescItems() : getTextDescItems();
  const finalStepIndex = isAllMediaFiles() ? 1 : 2;

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
            {currentStep > 0 && !(isAllMediaFiles() && currentStep === 1) && (
              <Button onClick={handlePrev}>
                {t("knowledgeBase.addData.confirm.previous")}
              </Button>
            )}
            {currentStep < finalStepIndex ? (
              <Button
                type="primary"
                disabled={getSelectedFilesCount() === 0 || (!isAllMediaFiles() && (!newKB.chunkSize || !newKB.overlapSize || !newKB.processType))}
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
          <Steps
            current={currentStep}
            size="small"
            items={steps}
            labelPlacement="vertical"
          />

          {currentStep === 0 && (
            <DatasetFileTransfer
              open={open}
              selectedFilesMap={selectedFilesMap}
              onSelectedFilesChange={setSelectedFilesMap}
              datasetTypeFilter={DatasetType.TEXT}
            />
          )}

          {!isAllMediaFiles() && (
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
                    rules={[{ required: true, message: t("knowledgeBase.addData.messages.validChunkSize") }]}
                  >
                    <Input type="number" placeholder={t("knowledgeBase.addData.form.chunkSizePlaceholder")} />
                  </Form.Item>
                  <Form.Item
                    label={t("knowledgeBase.addData.form.overlapLabel")}
                    name="overlapSize"
                    rules={[{ required: true, message: t("knowledgeBase.addData.messages.validOverlapSize") }]}
                  >
                    <Input type="number" placeholder={t("knowledgeBase.addData.form.overlapPlaceholder")} />
                  </Form.Item>
                </div>
                {newKB.processType === "CUSTOM_SEPARATOR_CHUNK" && (
                  <Form.Item
                    label={t("knowledgeBase.addData.form.delimiterLabel")}
                    name="delimiter"
                    rules={[{ required: true, message: t("knowledgeBase.addData.messages.inputDelimiter") }]}
                  >
                    <Input placeholder={t("knowledgeBase.addData.form.delimiterPlaceholder")} />
                  </Form.Item>
                )}
              </div>
            </Form>
          )}

          <div className="space-y-6" hidden={currentStep !== finalStepIndex}>
            <div className="text-lg font-medium mb-3">{t("knowledgeBase.addData.confirm.uploadConfirmTitle")}</div>
            <Descriptions layout="vertical" size="small" items={descItems} />
            <div className="text-sm text-yellow-600">
              {t("knowledgeBase.addData.confirm.uploadHint")}
            </div>
          </div>
        </div>
      </Modal>
    </>
  );
}
