import { useState } from "react";
import {
  Card,
  Steps,
  Select,
  Input,
  Button,
  Modal,
  Form,
  Tag,
  message,
} from "antd";
import { SaveOutlined, PlusOutlined } from "@ant-design/icons";
import { Link, useNavigate } from "react-router";
import { ArrowLeft, Database } from "lucide-react";
import OperatorLibrary from "./components/OperatorLibrary";
import OperatorOrchestration from "./components/OperatorOrchestration";
import OperatorConfig from "./components/OperatorConfig";
import { OPERATOR_CATEGORIES, operatorList } from "@/mock/cleansing";
import { datasetSubTypeMap } from "@/pages/DataManagement/dataset.const";
import { queryDatasetsUsingGet } from "@/pages/DataManagement/dataset.api";
import { useDragOperators } from "./hooks/useDragOperators";
import { useOperatorOperations } from "./hooks/useOperatorOperations";

const { TextArea } = Input;

export default function CleansingTaskCreate() {
  const navigate = useNavigate();
  const [taskConfig, setTaskConfig] = useState({
    name: "",
    description: "",
    datasetId: "",
    newDatasetName: "",
    priority: "normal",
    batchSize: "100",
    keepOriginal: true,
    generateReport: true,
    autoBackup: false,
  });
  const [showSaveTemplateDialog, setShowSaveTemplateDialog] = useState(false);
  const [templateName, setTemplateName] = useState("");
  const [templateDescription, setTemplateDescription] = useState("");
  const [datasets, setDatasets] = useState<any[]>([]);

  const {
    operators,
    selectedOperator,
    currentStep,
    templates,
    currentTemplate,
    setCurrentTemplate,
    setOperators,
    setSelectedOperator,
    toggleOperator,
    removeOperator,
    handleNext,
    handlePrev,
  } = useOperatorOperations();

  const {
    handleDragStart,
    handleDragEnd,
    handleContainerDragOver,
    handleContainerDragLeave,
    handleItemDragOver,
    handleItemDragLeave,
    handleItemDrop,
    handleDropToContainer,
  } = useDragOperators({ operators, setOperators });

  const fetchDatasets = async () => {
    const { data } = await queryDatasetsUsingGet({ page: 0, size: 1000 });
    setDatasets(data.content || []);
  };

  useState(() => {
    fetchDatasets();
  }, []);

  const handleSave = () => {
    const task = {
      ...taskConfig,
      operators,
      createdAt: new Date().toISOString(),
    };
    console.log("创建任务:", task);
    navigate("/data/cleansing");
    message.success("任务已创建");
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return (
          taskConfig.name && taskConfig.datasetId && taskConfig.newDatasetName
        );
      case 2:
        return operators.length > 0;
      default:
        return false;
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <Form layout="vertical">
            <h2 className="font-medium text-gray-900 text-lg mb-2">任务信息</h2>
            <Form.Item label="任务名称" required>
              <Input
                value={taskConfig.name}
                onChange={(e) =>
                  setTaskConfig({ ...taskConfig, name: e.target.value })
                }
                placeholder="输入清洗任务名称"
              />
            </Form.Item>
            <Form.Item label="任务描述">
              <TextArea
                value={taskConfig.description}
                onChange={(e) =>
                  setTaskConfig({ ...taskConfig, description: e.target.value })
                }
                placeholder="描述清洗任务的目标和要求"
                rows={4}
              />
            </Form.Item>
            <h2 className="font-medium text-gray-900 mt-4 mb-2 text-lg">
              数据源选择
            </h2>
            <Form.Item label="源数据集" required>
              <Select
                value={taskConfig.datasetId}
                onChange={(value) =>
                  setTaskConfig({ ...taskConfig, datasetId: value })
                }
                placeholder="请选择数据集"
                options={datasets.map((dataset) => ({
                  label: (
                    <div className="flex items-center justify-between gap-3 py-2">
                      <div className="flex items-center font-sm text-gray-900">
                        <span>
                          {dataset.icon || (
                            <Database className="w-4 h-4 mr-2" />
                          )}
                        </span>
                        <span>{dataset.name}</span>
                      </div>
                      <div className="text-xs text-gray-500">
                        {datasetSubTypeMap[dataset.type]?.label}
                      </div>
                    </div>
                  ),
                  value: dataset.id,
                }))}
              />
            </Form.Item>
            <Form.Item label="目标数据集名称" required>
              <Input
                value={taskConfig.newDatasetName}
                onChange={(e) =>
                  setTaskConfig({
                    ...taskConfig,
                    newDatasetName: e.target.value,
                  })
                }
                placeholder="输入目标数据集名称"
              />
            </Form.Item>
          </Form>
        );
      case 2:
        return (
          <div className="flex w-full h-full">
            {/* 左侧算子库 */}
            <OperatorLibrary
              operators={operators}
              operatorList={operatorList}
              OPERATOR_CATEGORIES={OPERATOR_CATEGORIES}
              toggleOperator={toggleOperator}
              handleDragStart={handleDragStart}
            />

            {/* 中间算子编排区域 */}
            <OperatorOrchestration
              operators={operators}
              selectedOperator={selectedOperator}
              templates={templates}
              currentTemplate={currentTemplate}
              setCurrentTemplate={setCurrentTemplate}
              setOperators={setOperators}
              OPERATOR_CATEGORIES={OPERATOR_CATEGORIES}
              setSelectedOperator={setSelectedOperator}
              removeOperator={removeOperator}
              handleDragStart={handleDragStart}
              handleContainerDragLeave={handleContainerDragLeave}
              handleContainerDragOver={handleContainerDragOver}
              handleItemDragOver={handleItemDragOver}
              handleItemDragLeave={handleItemDragLeave}
              handleItemDrop={handleItemDrop}
              handleDropToContainer={handleDropToContainer}
              handleDragEnd={handleDragEnd}
            />

            {/* 右侧参数配置面板 */}
            <OperatorConfig
              selectedOp={operators.find((op) => op.id === selectedOperator)}
            />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Link to="/data/cleansing">
            <Button type="text">
              <ArrowLeft className="w-4 h-4 mr-1" />
            </Button>
          </Link>
          <h1 className="text-xl font-bold">创建清洗任务</h1>
        </div>
        <div className="w-1/2">
          <Steps
            size="small"
            current={currentStep - 1}
            items={[{ title: "基本信息" }, { title: "算子编排" }]}
          />
        </div>
      </div>
      {/* Step Content */}
      <Card>
        {renderStepContent()}
        <div className="flex justify-end gap-3 mt-8">
          <Button onClick={() => navigate("/data/cleansing")}>取消</Button>
          {currentStep > 1 && <Button onClick={handlePrev}>上一步</Button>}
          {currentStep === 2 ? (
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSave}
              disabled={!canProceed()}
            >
              创建任务
            </Button>
          ) : (
            <Button
              type="primary"
              onClick={handleNext}
              disabled={!canProceed()}
            >
              下一步
            </Button>
          )}
        </div>
      </Card>

      {/* Save Template Dialog */}
      <Modal
        open={showSaveTemplateDialog}
        onCancel={() => setShowSaveTemplateDialog(false)}
        onOk={() => {}}
        okText="保存模板"
        cancelText="取消"
        title={
          <span>
            <PlusOutlined style={{ color: "#faad14", marginRight: 8 }} />
            保存为模板
          </span>
        }
      >
        <Form layout="vertical">
          <Form.Item label="模板名称" required>
            <Input
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              placeholder="输入模板名称"
            />
          </Form.Item>
          <Form.Item label="模板描述">
            <TextArea
              value={templateDescription}
              onChange={(e) => setTemplateDescription(e.target.value)}
              placeholder="描述模板的用途和特点"
              rows={3}
            />
          </Form.Item>
          <Form.Item label="包含算子">
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {operatorList.map((op, index) => (
                <Tag key={index}>{op.name}</Tag>
              ))}
            </div>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
