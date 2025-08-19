"use client"

import { useState } from "react"
import { Card, Steps, Select, Input, Button, Modal, Form, Typography, Tag, message } from "antd"
import { SaveOutlined, ArrowRightOutlined, DatabaseOutlined, PlusOutlined } from "@ant-design/icons"
import OperatorOrchestrationPage from "./components/Orchestration"
import { useNavigate } from "react-router"

const { TextArea } = Input
const { Title, Paragraph } = Typography

export default function CleansingTaskCreate() {
    const navigate = useNavigate();
    const [currentStep, setCurrentStep] = useState(1)
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
    })
    const [selectedOperators, setSelectedOperators] = useState<any[]>([])
    const [showSaveTemplateDialog, setShowSaveTemplateDialog] = useState(false)
    const [templateName, setTemplateName] = useState("")
    const [templateDescription, setTemplateDescription] = useState("")

    // 数据集列表
    const datasets = [
        { id: "1", name: "肺癌WSI病理图像数据集", type: "图像", files: 1250, size: "15.2GB" },
        { id: "2", name: "CT影像数据集", type: "医学影像", files: 800, size: "8.5GB" },
        { id: "3", name: "皮肤镜图像数据集", type: "图像", files: 600, size: "3.2GB" },
        { id: "4", name: "病理报告文本数据", type: "文本", files: 2000, size: "120MB" },
    ]

    const addOperator = (operator: any) => {
        const newOperator = {
            ...operator,
            id: `${operator.id}_${Date.now()}`,
            originalId: operator.id,
            config: Object.keys(operator.params || {}).reduce((acc: any, param: any) => {
                acc[param.name] = param.default
                return acc
            }, {}),
        }
        setSelectedOperators([...selectedOperators, newOperator])
    }

    const removeOperator = (id: string) => {
        setSelectedOperators(selectedOperators.filter((item) => item.id !== id))
    }

    const handleNext = () => {
        if (currentStep < 2) {
            setCurrentStep(currentStep + 1)
        }
    }

    const handlePrev = () => {
        if (currentStep > 1) {
            setCurrentStep(currentStep - 1)
        }
    }

    const handleSave = () => {
        const task = {
            ...taskConfig,
            operators: selectedOperators,
            createdAt: new Date().toISOString(),
        }
        onSave(task)
        message.success("任务已创建")
    }

    const canProceed = () => {
        switch (currentStep) {
            case 1:
                return taskConfig.name && taskConfig.datasetId && taskConfig.newDatasetName
            case 2:
                return selectedOperators.length > 0
            default:
                return false
        }
    }

    const renderStepContent = () => {
        switch (currentStep) {
            case 1:
                return (
                    <Form layout="vertical">
                        <Title level={4}>任务信息</Title>
                        <Form.Item label="任务名称 *" required>
                            <Input
                                value={taskConfig.name}
                                onChange={(e) => setTaskConfig({ ...taskConfig, name: e.target.value })}
                                placeholder="输入清洗任务名称"
                                size="large"
                            />
                        </Form.Item>
                        <Form.Item label="任务描述">
                            <TextArea
                                value={taskConfig.description}
                                onChange={(e) => setTaskConfig({ ...taskConfig, description: e.target.value })}
                                placeholder="描述清洗任务的目标和要求"
                                rows={4}
                            />
                        </Form.Item>
                        <Title level={4} style={{ marginTop: 32 }}>数据源选择</Title>
                        <Form.Item label="选择源数据集 *" required>
                            <Select
                                value={taskConfig.datasetId}
                                onChange={(value) => setTaskConfig({ ...taskConfig, datasetId: value })}
                                placeholder="请选择数据集"
                                size="large"
                                options={datasets.map((dataset) => ({
                                    label: (
                                        <div className="flex items-center gap-3 py-2">
                                            <DatabaseOutlined style={{ color: "#1677ff" }} />
                                            <div>
                                                <div className="font-medium text-gray-900">{dataset.name}</div>
                                                <div className="text-xs text-gray-500">
                                                    {dataset.files} 文件 • {dataset.size}
                                                </div>
                                            </div>
                                        </div>
                                    ),
                                    value: dataset.id,
                                }))}
                            />
                        </Form.Item>
                        <Form.Item label="处理后数据集名称 *" required>
                            <Input
                                value={taskConfig.newDatasetName}
                                onChange={(e) => setTaskConfig({ ...taskConfig, newDatasetName: e.target.value })}
                                placeholder="输入新数据集名称"
                                size="large"
                            />
                        </Form.Item>
                    </Form>
                )
            case 2:
                return (
                    <div>
                        <Title level={4}>算子编排</Title>
                        <OperatorOrchestrationPage handleAdd={addOperator} handleRemove={removeOperator} />
                    </div>
                )
            default:
                return null
        }
    }

    return (
        <div className="min-h-screen">
            <div className="space-y-8 px-4 py-8">
                {/* Header */}
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 24, width: "100%" }}>
                        <Button
                            type="text"
                            size="small"
                            onClick={() => navigate('/data/cleansing')}
                            style={{ marginRight: 16 }}
                            icon={<ArrowRightOutlined style={{ transform: "rotate(180deg)" }} />}
                        />
                        <div>
                            <Title level={3} style={{ margin: 0 }}>创建数据清洗任务</Title>
                            <Paragraph type="secondary" style={{ margin: 0 }}>配置任务参数并选择数据清洗算子</Paragraph>
                        </div>
                        <Steps
                            current={currentStep - 1}
                            items={[
                                { title: "基本信息" },
                                { title: "算子编排" },
                            ]}
                            style={{ width: "50%", marginLeft: "auto" }}
                        />
                    </div>
                </div>

                {/* Step Content */}
                <Card>
                    {renderStepContent()}
                    <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 32 }}>
                        <Button onClick={() => navigate('/data/cleansing')}>
                            取消
                        </Button>
                        {currentStep > 1 && (
                            <Button onClick={handlePrev}>
                                上一步
                            </Button>
                        )}
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
                    onOk={() => { }}
                    okText="保存模板"
                    cancelText="取消"
                    title={(
                        <span>
                            <PlusOutlined style={{ color: "#faad14", marginRight: 8 }} />
                            保存为模板
                        </span>
                    )}
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
                                {selectedOperators.map((op, index) => (
                                    <Tag key={index}>{op.name}</Tag>
                                ))}
                            </div>
                        </Form.Item>
                    </Form>
                </Modal>
            </div>
        </div>
    )
}