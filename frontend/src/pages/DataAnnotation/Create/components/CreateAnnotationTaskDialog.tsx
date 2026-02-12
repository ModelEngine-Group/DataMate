import { queryDatasetsUsingGet } from "@/pages/DataManagement/dataset.api";
import { mapDataset } from "@/pages/DataManagement/dataset.const";
import { Button, Form, Input, Modal, Select, message, Tabs, Slider, Checkbox } from "antd";
import TextArea from "antd/es/input/TextArea";
import { useEffect, useState } from "react";
import {
  createAnnotationTaskUsingPost,
  queryAnnotationTemplatesUsingGet,
  createAutoAnnotationTaskUsingPost,
} from "../../annotation.api";
import DatasetFileTransfer from "@/components/business/DatasetFileTransfer";
import { DatasetType, type Dataset, type DatasetFile } from "@/pages/DataManagement/dataset.model";
import type { AnnotationTemplate } from "../../annotation.model";
import { DataType } from "../../annotation.model";
import { useTranslation } from "react-i18next";

const { Option } = Select;

const COCO_CLASSES = [
  { id: 0, name: "person", label: "人" },
  { id: 1, name: "bicycle", label: "自行车" },
  { id: 2, name: "car", label: "汽车" },
  { id: 3, name: "motorcycle", label: "摩托车" },
  { id: 4, name: "airplane", label: "飞机" },
  { id: 5, name: "bus", label: "公交车" },
  { id: 6, name: "train", label: "火车" },
  { id: 7, name: "truck", label: "卡车" },
  { id: 8, name: "boat", label: "船" },
  { id: 9, name: "traffic light", label: "红绿灯" },
  { id: 10, name: "fire hydrant", label: "消防栓" },
  { id: 11, name: "stop sign", label: "停止标志" },
  { id: 12, name: "parking meter", label: "停车计时器" },
  { id: 13, name: "bench", label: "长椅" },
  { id: 14, name: "bird", label: "鸟" },
  { id: 15, name: "cat", label: "猫" },
  { id: 16, name: "dog", label: "狗" },
  { id: 17, name: "horse", label: "马" },
  { id: 18, name: "sheep", label: "羊" },
  { id: 19, name: "cow", label: "牛" },
  { id: 20, name: "elephant", label: "大象" },
  { id: 21, name: "bear", label: "熊" },
  { id: 22, name: "zebra", label: "斑马" },
  { id: 23, name: "giraffe", label: "长颈鹿" },
  { id: 24, name: "backpack", label: "背包" },
  { id: 25, name: "umbrella", label: "雨伞" },
  { id: 26, name: "handbag", label: "手提包" },
  { id: 27, name: "tie", label: "领带" },
  { id: 28, name: "suitcase", label: "行李箱" },
  { id: 29, name: "frisbee", label: "飞盘" },
  { id: 30, name: "skis", label: "滑雪板" },
  { id: 31, name: "snowboard", label: "滑雪板" },
  { id: 32, name: "sports ball", label: "球类" },
  { id: 33, name: "kite", label: "风筝" },
  { id: 34, name: "baseball bat", label: "棒球棒" },
  { id: 35, name: "baseball glove", label: "棒球手套" },
  { id: 36, name: "skateboard", label: "滑板" },
  { id: 37, name: "surfboard", label: "冲浪板" },
  { id: 38, name: "tennis racket", label: "网球拍" },
  { id: 39, name: "bottle", label: "瓶子" },
  { id: 40, name: "wine glass", label: "酒杯" },
  { id: 41, name: "cup", label: "杯子" },
  { id: 42, name: "fork", label: "叉子" },
  { id: 43, name: "knife", label: "刀" },
  { id: 44, name: "spoon", label: "勺子" },
  { id: 45, name: "bowl", label: "碗" },
  { id: 46, name: "banana", label: "香蕉" },
  { id: 47, name: "apple", label: "苹果" },
  { id: 48, name: "sandwich", label: "三明治" },
  { id: 49, name: "orange", label: "橙子" },
  { id: 50, name: "broccoli", label: "西兰花" },
  { id: 51, name: "carrot", label: "胡萝卜" },
  { id: 52, name: "hot dog", label: "热狗" },
  { id: 53, name: "pizza", label: "披萨" },
  { id: 54, name: "donut", label: "甜甜圈" },
  { id: 55, name: "cake", label: "蛋糕" },
  { id: 56, name: "chair", label: "椅子" },
  { id: 57, name: "couch", label: "沙发" },
  { id: 58, name: "potted plant", label: "盆栽" },
  { id: 59, name: "bed", label: "床" },
  { id: 60, name: "dining table", label: "餐桌" },
  { id: 61, name: "toilet", label: "马桶" },
  { id: 62, name: "tv", label: "电视" },
  { id: 63, name: "laptop", label: "笔记本电脑" },
  { id: 64, name: "mouse", label: "鼠标" },
  { id: 65, name: "remote", label: "遥控器" },
  { id: 66, name: "keyboard", label: "键盘" },
  { id: 67, name: "cell phone", label: "手机" },
  { id: 68, name: "microwave", label: "微波炉" },
  { id: 69, name: "oven", label: "烤箱" },
  { id: 70, name: "toaster", label: "烤面包机" },
  { id: 71, name: "sink", label: "水槽" },
  { id: 72, name: "refrigerator", label: "冰箱" },
  { id: 73, name: "book", label: "书" },
  { id: 74, name: "clock", label: "钟表" },
  { id: 75, name: "vase", label: "花瓶" },
  { id: 76, name: "scissors", label: "剪刀" },
  { id: 77, name: "teddy bear", label: "玩具熊" },
  { id: 78, name: "hair drier", label: "吹风机" },
  { id: 79, name: "toothbrush", label: "牙刷" },
];

export default function CreateAnnotationTask({
  open,
  onClose,
  onRefresh,
}: {
  open: boolean;
  onClose: () => void;
  onRefresh: () => void;
}) {
  const { t } = useTranslation();
  const [manualForm] = Form.useForm();
  const [autoForm] = Form.useForm();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [templates, setTemplates] = useState<AnnotationTemplate[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [nameManuallyEdited, setNameManuallyEdited] = useState(false);
  const [activeMode, setActiveMode] = useState<"manual" | "auto">("manual");

  const [selectAllClasses, setSelectAllClasses] = useState(true);
  const [selectedFilesMap, setSelectedFilesMap] = useState<Record<string, DatasetFile>>({});
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [imageFileCount, setImageFileCount] = useState(0);
  const [manualDatasetTypeFilter, setManualDatasetTypeFilter] = useState<DatasetType | undefined>(undefined);
  const [manualAllowedExtensions, setManualAllowedExtensions] = useState<string[] | undefined>(undefined);

  useEffect(() => {
    if (!open) return;
    const fetchData = async () => {
      try {
        // Fetch datasets
        const { data: datasetData } = await queryDatasetsUsingGet({
          page: 0,
          pageSize: 1000,  // Use camelCase for HTTP params
        });
        setDatasets(datasetData.content.map(dataset => mapDataset(dataset, t)) || []);

        // Fetch templates
        const templateResponse = await queryAnnotationTemplatesUsingGet({
          page: 1,
          size: 100,  // Backend max is 100 (template API uses 'size' not 'pageSize')
        });

        // The API returns: {code, message, data: {content, total, page, ...}}
        if (templateResponse.data) {
          const fetchedTemplates = templateResponse.data.content || [];
          console.log("Fetched templates:", fetchedTemplates);
          setTemplates(fetchedTemplates);
        } else {
          console.error("Failed to fetch templates:", templateResponse);
          setTemplates([]);
        }
      } catch (error) {
        console.error("Error fetching data:", error);
        setTemplates([]);
      }
    };
    fetchData();
  }, [open]);

  // Reset form and manual-edit flag when modal opens
  useEffect(() => {
    if (open) {
      manualForm.resetFields();
      autoForm.resetFields();
      setNameManuallyEdited(false);
      setActiveMode("manual");
      setSelectAllClasses(true);
      setSelectedFilesMap({});
      setSelectedDataset(null);
      setImageFileCount(0);
    }
  }, [open, manualForm, autoForm]);

  useEffect(() => {
    const imageExtensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"];
    const count = Object.values(selectedFilesMap).filter((file) => {
      const ext = file.fileName?.toLowerCase().match(/\.[^.]+$/)?.[0] || "";
      return imageExtensions.includes(ext);
    }).length;
    setImageFileCount(count);
  }, [selectedFilesMap]);

  const IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp", ".h5", ".pt"];
  const TEXT_EXTENSIONS = [".txt", ".md", ".csv", ".tsv", ".jsonl", ".log"];
  const AUDIO_EXTENSIONS = [".wav", ".mp3", ".flac", ".aac", ".ogg", ".m4a", ".wma"];
  const VIDEO_EXTENSIONS = [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"];

  const mapTemplateDataTypeToDatasetType = (raw?: string): DatasetType | undefined => {
    if (!raw) return undefined;
    const v = String(raw).trim().toLowerCase();

    // 兼容多种表示方式：
    // - 英文大写/小写：IMAGE / image / Text / TEXT
    // - 后端枚举 DataType：text / image / audio / video
    // - 中文展示文案：图像 / 文本 / 音频 / 视频
    // - 少量常见别称：图片 等

    const textTokens = new Set([
      "text",
      DataType.TEXT.toLowerCase(),
      "文本",
    ]);
    const imageTokens = new Set([
      "image",
      DataType.IMAGE.toLowerCase(),
      "图像",
      "图片",
    ]);
    const audioTokens = new Set([
      "audio",
      DataType.AUDIO.toLowerCase(),
      "音频",
    ]);
    const videoTokens = new Set([
      "video",
      DataType.VIDEO.toLowerCase(),
      "视频",
    ]);

    if (textTokens.has(v)) return DatasetType.TEXT;
    if (imageTokens.has(v)) return DatasetType.IMAGE;
    if (audioTokens.has(v)) return DatasetType.AUDIO;
    if (videoTokens.has(v)) return DatasetType.VIDEO;

    return undefined;
  };

  const getAllowedExtensionsForTemplateDataType = (raw?: string): string[] | undefined => {
    if (!raw) return undefined;
    const v = String(raw).trim().toLowerCase();

    const textTokens = new Set<string>([
      "text",
      DataType.TEXT.toLowerCase(),
      "文本",
    ]);
    const imageTokens = new Set<string>([
      "image",
      DataType.IMAGE.toLowerCase(),
      "图像",
      "图片",
    ]);
    const audioTokens = new Set<string>([
      "audio",
      DataType.AUDIO.toLowerCase(),
      "音频",
    ]);
    const videoTokens = new Set<string>([
      "video",
      DataType.VIDEO.toLowerCase(),
      "视频",
    ]);

    if (textTokens.has(v)) return TEXT_EXTENSIONS;
    if (imageTokens.has(v)) return IMAGE_EXTENSIONS;
    if (audioTokens.has(v)) return AUDIO_EXTENSIONS;
    if (videoTokens.has(v)) return VIDEO_EXTENSIONS;

    return undefined;
  };

  const handleManualSubmit = async () => {
    try {
      const values = await manualForm.validateFields();
      setSubmitting(true);
      // 手动标注也支持跨数据集、精确到文件的选择
      const selectedFiles = Object.values(selectedFilesMap) as any[];

      if (selectedFiles.length === 0) {
        message?.error?.(t('dataAnnotation.create.messages.selectAtLeastOneFile'));
        setSubmitting(false);
        return;
      }

      const datasetIds = Array.from(
        new Set(
          selectedFiles
            .map((file) => file?.datasetId)
            .filter((id) => id !== undefined && id !== null && id !== ""),
        ),
      );

      const effectiveDatasetId = values.datasetId || datasetIds[0];

      // Send templateId and fileIds；后端会按 fileIds 反查真实数据集并同步到同一 LS 工程
      const requestData = {
        name: values.name,
        description: values.description,
        datasetId: effectiveDatasetId,
        templateId: values.templateId,
        fileIds: selectedFiles.map((file) => file.id),
      };

      await createAnnotationTaskUsingPost(requestData);
      message?.success?.(t('dataAnnotation.create.messages.createSuccess'));
      onClose();
      onRefresh();
    } catch (err: any) {
      console.error("Create annotation task failed", err);
      const msg = err?.message || err?.data?.message || t('dataAnnotation.create.messages.createFailed');
      (message as any)?.error?.(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleAutoSubmit = async () => {
    try {
      const values = await autoForm.validateFields();

      if (imageFileCount === 0) {
        message.error(t('dataAnnotation.create.messages.selectAtLeastOneImageFile'));
        return;
      }

      setSubmitting(true);

      const selectedFiles = Object.values(selectedFilesMap) as any[];

      // 对于自动标注，后端会根据 fileIds 自动按数据集分组并为每个数据集创建/复用 LS 项目，
      // 这里不再强制限制只能选择单一数据集，只需保证至少有一个 datasetId，
      // 否则退回到表单中的 datasetId。
      const datasetIds = Array.from(
        new Set(
          selectedFiles
            .map((file) => file?.datasetId)
            .filter((id) => id !== undefined && id !== null && id !== ""),
        ),
      );

      const effectiveDatasetId = values.datasetId || datasetIds[0];

      const imageExtensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"];
      const imageFileIds = Object.values(selectedFilesMap)
        .filter((file) => {
          const ext = file.fileName?.toLowerCase().match(/\.[^.]+$/)?.[0] || "";
          return imageExtensions.includes(ext);
        })
        .map((file) => file.id);

      const payload = {
        name: values.name,
        datasetId: effectiveDatasetId,
        fileIds: imageFileIds,
        config: {
          modelSize: values.modelSize,
          confThreshold: values.confThreshold,
          targetClasses: selectAllClasses ? [] : values.targetClasses || [],
        },
      };

      await createAutoAnnotationTaskUsingPost(payload);
      message.success(t('dataAnnotation.create.messages.autoCreateSuccess'));
      // 触发上层刷新自动标注任务列表
      (onRefresh as any)?.("auto");
      onClose();
    } catch (error: any) {
      if (error.errorFields) return;
      console.error("Failed to create auto annotation task:", error);
      message.error(error.message || t('dataAnnotation.create.messages.autoCreateFailed'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleClassSelectionChange = (checked: boolean) => {
    setSelectAllClasses(checked);
    if (checked) {
      autoForm.setFieldsValue({ targetClasses: [] });
    }
  };

  return (
    <Modal
      open={open}
      onCancel={onClose}
      title={t('dataAnnotation.create.title')}
      footer={
        <>
          <Button onClick={onClose} disabled={submitting}>
            {t('dataAnnotation.create.cancel')}
          </Button>
          <Button
            type="primary"
            onClick={activeMode === "manual" ? handleManualSubmit : handleAutoSubmit}
            loading={submitting}
          >
            {t('dataAnnotation.create.ok')}
          </Button>
        </>
      }
      width={800}
    >
      <Tabs
        activeKey={activeMode}
        onChange={(key) => setActiveMode(key as "manual" | "auto")}
        items={[
          {
            key: "manual",
            label: t('dataAnnotation.create.manual'),
            children: (
              <Form form={manualForm} layout="vertical">
                {/* 任务名称放在第一行，必填 */}
                <Form.Item
                  label={t('dataAnnotation.create.form.name')}
                  name="name"
                  rules={[
                    {
                      required: true,
                      validator: (_rule, value) => {
                        const trimmed = (value || "").trim();
                        if (!trimmed) {
                          return Promise.reject(new Error(t('dataAnnotation.create.form.nameRequired')));
                        }
                        if (trimmed.length < 3) {
                          return Promise.reject(
                            new Error(t('dataAnnotation.create.form.nameMinLength')),
                          );
                        }
                        return Promise.resolve();
                      },
                    },
                  ]}
                >
                  <Input
                    placeholder={t('dataAnnotation.create.form.namePlaceholder')}
                    onChange={() => setNameManuallyEdited(true)}
                  />
                </Form.Item>

                {/* 第二行：先选模板，再选数据集，模板的数据类型驱动可选数据集类型 */}
                <Form.Item
                  label={t('dataAnnotation.create.form.template')}
                  name="templateId"
                  rules={[{ required: true, message: t('dataAnnotation.create.form.templateRequired') }]}
                >
                  <Select
                    placeholder={templates.length === 0 ? t('dataAnnotation.create.form.noTemplatesAvailable') : t('dataAnnotation.create.form.selectTemplate')}
                    showSearch
                    optionFilterProp="label"
                    notFoundContent={templates.length === 0 ? t('dataAnnotation.create.form.noTemplatesFound') : t('dataAnnotation.create.form.noTemplatesAvailable')}
                    options={templates
                      .filter((template) => {
                        const tplType = mapTemplateDataTypeToDatasetType(template.dataType);
                        if (!selectedDataset || !selectedDataset.datasetType) return true;
                        if (!tplType) return true;
                        return tplType === selectedDataset.datasetType;
                      })
                      .map((template) => ({
                        label: template.name,
                        value: template.id,
                        title: template.description,
                      }))}
                    onChange={(value) => {
                      manualForm.setFieldsValue({ templateId: value });

                      const tpl = templates.find((t) => t.id === value);
                      const nextType = mapTemplateDataTypeToDatasetType(tpl?.dataType);
                      setManualDatasetTypeFilter(nextType);

                      const nextExtensions = getAllowedExtensionsForTemplateDataType(tpl?.dataType);
                      setManualAllowedExtensions(nextExtensions);

                      // 若当前已选数据集类型与模板不匹配，则清空当前选择
                      if (selectedDataset && nextType && selectedDataset.datasetType !== nextType) {
                        setSelectedDataset(null);
                        setSelectedFilesMap({});
                        manualForm.setFieldsValue({ datasetId: "" });
                        message.warning(t('dataAnnotation.create.messages.datasetTypeFiltered'));
                      }
                    }}
                    optionRender={(option) => (
                      <div>
                        <div style={{ fontWeight: 500 }}>{option.label}</div>
                        {option.data.title && (
                          <div style={{ fontSize: 12, color: '#999', marginTop: 2 }}>
                            {option.data.title}
                          </div>
                        )}
                      </div>
                    )}
                  />
                </Form.Item>

                {/* 选择数据集和文件（仅允许单一数据集，多文件），需先选模板再操作 */}
                <Form.Item label={t('dataAnnotation.create.form.selectDatasetAndFiles')} required>
                  <DatasetFileTransfer
                    open
                    selectedFilesMap={selectedFilesMap}
                    onSelectedFilesChange={setSelectedFilesMap}
                    onDatasetSelect={(dataset) => {
                      setSelectedDataset(dataset as Dataset | null);
                      // 将当前数据集写入隐藏字段，作为主数据集ID
                      manualForm.setFieldsValue({ datasetId: dataset?.id ?? "" });

                      // 如果用户未手动修改名称，则用当前数据集名称作为默认任务名
                      if (!nameManuallyEdited && dataset) {
                        let defaultName = dataset.name || "";
                        if (defaultName.length < 3) {
                          defaultName = `${defaultName}-标注`;
                        }
                        manualForm.setFieldsValue({ name: defaultName });
                      }
                    }}
                    datasetTypeFilter={manualDatasetTypeFilter}
                    allowedFileExtensions={manualAllowedExtensions}
                    singleDatasetOnly
                    disabled={!manualForm.getFieldValue("templateId")}
                  />
                  {selectedDataset && (
                    <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200 text-xs">
                      {t('dataAnnotation.create.form.currentDataset', { name: selectedDataset.name, count: Object.keys(selectedFilesMap).length })}
                    </div>
                  )}
                </Form.Item>

                {/* 隐藏的主数据集ID，用于后端兼容老字段 */}
                <Form.Item
                  hidden
                  name="datasetId"
                  rules={[{ required: true, message: t('dataAnnotation.create.form.datasetRequired') }]}
                >
                  <Input type="hidden" />
                </Form.Item>
                {/* 描述变为可选 */}
                <Form.Item label={t('dataAnnotation.create.form.description')} name="description">
                  <TextArea placeholder={t('dataAnnotation.create.form.descriptionPlaceholder')} rows={3} />
                </Form.Item>
              </Form>
            ),
          },
          {
            key: "auto",
            label: t('dataAnnotation.create.auto'),
            children: (
              <Form form={autoForm} layout="vertical" preserve={false}>
                {/* 自动标注：任务名称仍然放在第一行，必填 */}
                <Form.Item
                  name="name"
                  label={t('dataAnnotation.create.form.name')}
                  rules={[
                    { required: true, message: t('dataAnnotation.create.form.nameRequired') },
                    { max: 100, message: t('dataAnnotation.create.form.nameMaxLength') },
                  ]}
                >
                  <Input placeholder={t('dataAnnotation.create.form.namePlaceholder')} />
                </Form.Item>

                <Form.Item label={t('dataAnnotation.create.form.selectDatasetAndFiles')} required>
                  <DatasetFileTransfer
                    open
                    selectedFilesMap={selectedFilesMap}
                    onSelectedFilesChange={setSelectedFilesMap}
                    onDatasetSelect={(dataset) => {
                      setSelectedDataset(dataset as Dataset | null);
                      autoForm.setFieldsValue({ datasetId: dataset?.id ?? "" });
                    }}
                    datasetTypeFilter={DatasetType.IMAGE}
                    allowedFileExtensions={IMAGE_EXTENSIONS}
                    singleDatasetOnly
                  />
                  {selectedDataset && (
                    <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200 text-xs">
                      {t('dataAnnotation.create.form.currentDataset', { name: selectedDataset.name, count: imageFileCount })}
                    </div>
                  )}
                </Form.Item>

                <Form.Item
                  hidden
                  name="datasetId"
                  rules={[{ required: true, message: t('dataAnnotation.create.form.datasetRequired') }]}
                >
                  <Input type="hidden" />
                </Form.Item>

                <Form.Item
                  name="modelSize"
                  label={t('dataAnnotation.create.form.modelSize')}
                  rules={[{ required: true, message: t('dataAnnotation.create.form.modelSizeRequired') }]}
                  initialValue="l"
                >
                  <Select>
                    <Option value="n">{t('dataAnnotation.home.autoModelSizeLabels.n')}</Option>
                    <Option value="s">{t('dataAnnotation.home.autoModelSizeLabels.s')}</Option>
                    <Option value="m">{t('dataAnnotation.home.autoModelSizeLabels.m')}</Option>
                    <Option value="l">{t('dataAnnotation.home.autoModelSizeLabels.l')}</Option>
                    <Option value="x">{t('dataAnnotation.home.autoModelSizeLabels.x')}</Option>
                  </Select>
                </Form.Item>

                <Form.Item
                  name="confThreshold"
                  label={t('dataAnnotation.create.form.confThreshold')}
                  rules={[{ required: true, message: t('dataAnnotation.create.form.confThresholdRequired') }]}
                  initialValue={0.7}
                >
                  <Slider
                    min={0.1}
                    max={0.9}
                    step={0.05}
                    tooltip={{ formatter: (v) => `${(v || 0) * 100}%` }}
                  />
                </Form.Item>

                <Form.Item label={t('dataAnnotation.create.form.targetClasses')}>
                  <Checkbox
                    checked={selectAllClasses}
                    onChange={(e) => handleClassSelectionChange(e.target.checked)}
                  >
                    {t('dataAnnotation.create.form.selectAllClasses')}
                  </Checkbox>
                  {!selectAllClasses && (
                    <Form.Item name="targetClasses" noStyle>
                      <Select mode="multiple" placeholder={t('dataAnnotation.create.form.selectTargetClasses')} style={{ marginTop: 8 }}>
                        {COCO_CLASSES.map((cls) => (
                          <Option key={cls.id} value={cls.id}>
                            {cls.label} ({cls.name})
                          </Option>
                        ))}
                      </Select>
                    </Form.Item>
                  )}
                </Form.Item>
              </Form>
            ),
          },
        ]}
      />
    </Modal>
  );
}
