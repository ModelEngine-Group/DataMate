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
import { DatasetFileCols } from "../knowledge-base.const";

const sliceOptions = [
  { label: "默认分块", value: "DEFAULT_CHUNK" },
  { label: "章节分块", value: "CHAPTER_CHUNK" },
  { label: "段落分块", value: "PARAGRAPH_CHUNK" },
  { label: "长度分块", value: "LENGTH_CHUNK" },
  { label: "自定义分割符分块", value: "CUSTOM_SEPARATOR_CHUNK" },
];

export default function AddDataDialog({ knowledgeBase, onDataAdded }) {
  const [open, setOpen] = useState(false);
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const [currentStep, setCurrentStep] = useState(0);

  const [selectedFilesMap, setSelectedFilesMap] = useState({});

  // 定义分块选项
  const sliceOptions = [
    { label: "默认分块", value: "DEFAULT_CHUNK" },
    { label: "按章节分块", value: "CHAPTER_CHUNK" },
    { label: "按段落分块", value: "PARAGRAPH_CHUNK" },
    { label: "固定长度分块", value: "FIXED_LENGTH_CHUNK" },
    { label: "自定义分隔符分块", value: "CUSTOM_SEPARATOR_CHUNK" },
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
      title: "选择数据集文件",
      description: "从多个数据集中选择文件",
    },
    {
      title: "配置参数",
      description: "设置数据处理参数",
    },
    {
      title: "确认上传",
      description: "确认信息并上传",
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
        message.warning("请至少选择一个文件");
        return;
      }
    }
    if (currentStep === 1) {
      // 验证切片参数
      if (!newKB.processType) {
        message.warning("请选择分块方式");
        return;
      }
      if (!newKB.chunkSize || Number(newKB.chunkSize) <= 0) {
        message.warning("请输入有效的分块大小");
        return;
      }
      if (!newKB.overlapSize || Number(newKB.overlapSize) < 0) {
        message.warning("请输入有效的重叠长度");
        return;
      }
      if (newKB.processType === "CUSTOM_SEPARATOR_CHUNK" && !newKB.delimiter) {
        message.warning("请输入分隔符");
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
      message.warning("请至少选择一个文件");
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

      message.success("数据添加成功");
      // 重置状态
      setOpen(false);
    } catch (error) {
      message.error("数据添加失败，请重试");
      console.error("添加文件失败:", error);
    }
  };

  const handleModalCancel = () => {
    setOpen(false);
  };

  const descItems: DescriptionsItemType[] = [
    {
      label: "知识库名称",
      key: "knowledgeBaseName",
      children: knowledgeBase?.name,
    },
    {
      label: "数据来源",
      key: "dataSource",
      children: "数据集",
    },
    {
      label: "文件总数",
      key: "totalFileCount",
      children: Object.keys(selectedFilesMap).length,
    },
    {
      label: "分块方式",
      key: "chunkingMethod",
      children:
        sliceOptions.find((opt) => opt.value === newKB.processType)?.label ||
        "",
    },
    {
      label: "分块大小",
      key: "chunkSize",
      children: newKB.chunkSize,
    },
    {
      label: "重叠长度",
      key: "overlapSize",
      children: newKB.overlapSize,
    },
    ...(newKB.processType === "CUSTOM_SEPARATOR_CHUNK" && newKB.delimiter
      ? [
          {
            label: "分隔符",
            children: <span className="font-mono">{newKB.delimiter}</span>,
          },
        ]
      : []),
    {
      label: "文件列表",
      key: "fileList",
      span: 3,
      children: (
        <Table
          scroll={{ y: 400 }}
          rowKey="id"
          size="small"
          dataSource={Object.values(selectedFilesMap)}
          columns={DatasetFileCols}
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
        添加数据
      </Button>
      <Modal
        title="添加数据"
        open={open}
        onCancel={handleModalCancel}
        footer={
          <div className="space-x-2">
            {currentStep === 0 && (
              <Button onClick={handleModalCancel}>取消</Button>
            )}
            {currentStep > 0 && (
              <Button disabled={false} onClick={handlePrev}>
                上一步
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
                下一步
              </Button>
            ) : (
              <Button type="primary" onClick={handleAddData}>
                确认上传
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
                label="分块方式"
                name="processType"
                required
                rules={[{ required: true }]}
              >
                <Select options={sliceOptions} />
              </Form.Item>

              <div className="grid grid-cols-2 gap-6">
                <Form.Item
                  label="分块大小"
                  name="chunkSize"
                  rules={[
                    {
                      required: true,
                      message: "请输入分块大小",
                    },
                  ]}
                >
                  <Input type="number" placeholder="请输入分块大小" />
                </Form.Item>
                <Form.Item
                  label="重叠长度"
                  name="overlapSize"
                  rules={[
                    {
                      required: true,
                      message: "请输入重叠长度",
                    },
                  ]}
                >
                  <Input type="number" placeholder="请输入重叠长度" />
                </Form.Item>
              </div>

              {newKB.processType === "CUSTOM_SEPARATOR_CHUNK" && (
                <Form.Item
                  label="分隔符"
                  name="delimiter"
                  rules={[
                    {
                      required: true,
                      message: "请输入分隔符",
                    },
                  ]}
                >
                  <Input placeholder="输入分隔符，如 \n\n" />
                </Form.Item>
              )}
            </div>
          </Form>

          <div className="space-y-6" hidden={currentStep !== 2}>
            <div className="">
              <div className="text-lg font-medium mb-3">上传信息确认</div>
              <Descriptions layout="vertical" size="small" items={descItems} />
            </div>
            <div className="text-sm text-yellow-600">
              提示：上传后系统将自动处理文件，请耐心等待
            </div>
          </div>
        </div>
      </Modal>
    </>
  );
}
