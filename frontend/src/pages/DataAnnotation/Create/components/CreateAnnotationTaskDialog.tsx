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

  useEffect(() => {
    if (!open) return;
    const fetchData = async () => {
      try {
        // Fetch datasets
        const { data: datasetData } = await queryDatasetsUsingGet({
          page: 0,
          pageSize: 1000,  // Use camelCase for HTTP params
        });
        setDatasets(datasetData.content.map(mapDataset) || []);

        // Fetch templates
        const templateResponse = await queryAnnotationTemplatesUsingGet({
          page: 1,
          size: 100,  // Backend max is 100 (template API uses 'size' not 'pageSize')
        });

        // The API returns: {code, message, data: {content, total, page, ...}}
        if (templateResponse.code === 200 && templateResponse.data) {
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

  const handleManualSubmit = async () => {
    try {
      const values = await manualForm.validateFields();
      setSubmitting(true);
      // 手动标注也支持跨数据集、精确到文件的选择
      const selectedFiles = Object.values(selectedFilesMap) as any[];

      const imageExtensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"];
      const imageFileIds = selectedFiles
        .filter((file) => {
          const ext = file.fileName?.toLowerCase().match(/\.[^.]+$/)?.[0] || "";
          return imageExtensions.includes(ext);
        })
        .map((file) => file.id);

      if (imageFileIds.length === 0) {
        message?.error?.("请至少选择一个图像文件");
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
        fileIds: imageFileIds,
      };

      await createAnnotationTaskUsingPost(requestData);
      message?.success?.("创建标注任务成功");
      onClose();
      onRefresh();
    } catch (err: any) {
      console.error("Create annotation task failed", err);
      const msg = err?.message || err?.data?.message || "创建失败，请稍后重试";
      (message as any)?.error?.(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleAutoSubmit = async () => {
    try {
      const values = await autoForm.validateFields();

      if (imageFileCount === 0) {
        message.error("请至少选择一个图像文件");
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
          outputDatasetName: values.outputDatasetName || undefined,
        },
      };

      await createAutoAnnotationTaskUsingPost(payload);
      message.success("自动标注任务创建成功");
      // 触发上层刷新自动标注任务列表
      (onRefresh as any)?.("auto");
      onClose();
    } catch (error: any) {
      if (error.errorFields) return;
      console.error("Failed to create auto annotation task:", error);
      message.error(error.message || "创建自动标注任务失败");
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
      title="创建标注任务"
      footer={
        <>
          <Button onClick={onClose} disabled={submitting}>
            取消
          </Button>
          <Button
            type="primary"
            onClick={activeMode === "manual" ? handleManualSubmit : handleAutoSubmit}
            loading={submitting}
          >
            确定
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
            label: "手动标注",
            children: (
              <Form form={manualForm} layout="vertical">
                {/* 选择数据集和图像文件（支持多数据集、多文件） */}
                <Form.Item label="选择数据集和图像文件" required>
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
                    datasetTypeFilter={DatasetType.IMAGE}
                  />
                  {selectedDataset && (
                    <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200 text-xs">
                      当前数据集：<span className="font-medium">{selectedDataset.name}</span> - 已选择
                      <span className="font-medium text-blue-600"> {imageFileCount} </span>个图像文件
                    </div>
                  )}
                </Form.Item>

                {/* 隐藏的主数据集ID，用于后端兼容老字段 */}
                <Form.Item
                  hidden
                  name="datasetId"
                  rules={[{ required: true, message: "请选择数据集" }]}
                >
                  <Input type="hidden" />
                </Form.Item>

                {/* 标注工程名称 */}
                <Form.Item
                  label="标注工程名称"
                  name="name"
                  rules={[
                    {
                      validator: (_rule, value) => {
                        const trimmed = (value || "").trim();
                        if (!trimmed) {
                          return Promise.reject(new Error("请输入任务名称"));
                        }
                        if (trimmed.length < 3) {
                          return Promise.reject(
                            new Error("任务名称至少需要 3 个字符（不含首尾空格，Label Studio 限制）"),
                          );
                        }
                        return Promise.resolve();
                      },
                    },
                  ]}
                >
                  <Input
                    placeholder="输入标注工程名称"
                    onChange={() => setNameManuallyEdited(true)}
                  />
                </Form.Item>
                {/* 描述变为可选 */}
                <Form.Item label="描述" name="description">
                  <TextArea placeholder="（可选）详细描述标注任务的要求和目标" rows={3} />
                </Form.Item>

                {/* 标注模板选择 */}
                <Form.Item
                  label="标注模板"
                  name="templateId"
                  rules={[{ required: true, message: "请选择标注模板" }]}
                >
                  <Select
                    placeholder={templates.length === 0 ? "暂无可用模板，请先创建模板" : "请选择标注模板"}
                    showSearch
                    optionFilterProp="label"
                    notFoundContent={templates.length === 0 ? "暂无模板，请前往「标注模板」页面创建" : "未找到匹配的模板"}
                    options={templates.map((template) => ({
                      label: template.name,
                      value: template.id,
                      // Add description as subtitle
                      title: template.description,
                    }))}
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
              </Form>
            ),
          },
          {
            key: "auto",
            label: "自动标注",
            children: (
              <Form form={autoForm} layout="vertical" preserve={false}>
                <Form.Item
                  name="name"
                  label="任务名称"
                  rules={[
                    { required: true, message: "请输入任务名称" },
                    { max: 100, message: "任务名称不能超过100个字符" },
                  ]}
                >
                  <Input placeholder="请输入任务名称" />
                </Form.Item>

                <Form.Item label="选择数据集和图像文件" required>
                  <DatasetFileTransfer
                    open
                    selectedFilesMap={selectedFilesMap}
                    onSelectedFilesChange={setSelectedFilesMap}
                    onDatasetSelect={(dataset) => {
                      setSelectedDataset(dataset as Dataset | null);
                      autoForm.setFieldsValue({ datasetId: dataset?.id ?? "" });
                    }}
                    datasetTypeFilter={DatasetType.IMAGE}
                  />
                  {selectedDataset && (
                    <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200 text-xs">
                      当前数据集：<span className="font-medium">{selectedDataset.name}</span> - 已选择
                      <span className="font-medium text-blue-600"> {imageFileCount} </span>个图像文件
                    </div>
                  )}
                </Form.Item>

                <Form.Item
                  hidden
                  name="datasetId"
                  rules={[{ required: true, message: "请选择数据集" }]}
                >
                  <Input type="hidden" />
                </Form.Item>

                <Form.Item
                  name="modelSize"
                  label="模型规模"
                  rules={[{ required: true, message: "请选择模型规模" }]}
                  initialValue="l"
                >
                  <Select>
                    <Option value="n">YOLOv8n (最快)</Option>
                    <Option value="s">YOLOv8s</Option>
                    <Option value="m">YOLOv8m</Option>
                    <Option value="l">YOLOv8l (推荐)</Option>
                    <Option value="x">YOLOv8x (最精确)</Option>
                  </Select>
                </Form.Item>

                <Form.Item
                  name="confThreshold"
                  label="置信度阈值"
                  rules={[{ required: true, message: "请选择置信度阈值" }]}
                  initialValue={0.7}
                >
                  <Slider
                    min={0.1}
                    max={0.9}
                    step={0.05}
                    tooltip={{ formatter: (v) => `${(v || 0) * 100}%` }}
                  />
                </Form.Item>

                <Form.Item label="目标类别">
                  <Checkbox
                    checked={selectAllClasses}
                    onChange={(e) => handleClassSelectionChange(e.target.checked)}
                  >
                    选中所有类别
                  </Checkbox>
                  {!selectAllClasses && (
                    <Form.Item name="targetClasses" noStyle>
                      <Select mode="multiple" placeholder="选择目标类别" style={{ marginTop: 8 }}>
                        {COCO_CLASSES.map((cls) => (
                          <Option key={cls.id} value={cls.id}>
                            {cls.label} ({cls.name})
                          </Option>
                        ))}
                      </Select>
                    </Form.Item>
                  )}
                </Form.Item>

                <Form.Item name="outputDatasetName" label="输出数据集名称 (可选)">
                  <Input placeholder="留空则将结果写入原数据集的标签中" />
                </Form.Item>
              </Form>
            ),
          },
        ]}
      />
    </Modal>
  );
}
