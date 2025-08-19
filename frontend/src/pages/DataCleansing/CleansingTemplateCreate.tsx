"use client"

import { useState } from "react"
import { Card, Button, Input, Badge, Steps, Form } from "antd"
import { CheckCircleOutlined, ArrowRightOutlined } from "@ant-design/icons"
import OperatorOrchestrationPage from "./components/Orchestration"
import { useNavigate } from "react-router"

const { TextArea } = Input

export default function CleansingTemplateCreate() {
    const navigate = useNavigate();
    const [currentStep, setCurrentStep] = useState(0)
    const [templateConfig, setTemplateConfig] = useState({
        name: "",
        description: "",
        type: "",
        category: "",
    })
    const [selectedOperators, setSelectedOperators] = useState<any[]>([])

    // 模板类型选项
    const templateTypes = [
        { value: "text", label: "文本", icon: "📝", description: "处理文本数据的清洗模板" },
        { value: "image", label: "图片", icon: "🖼️", description: "处理图像数据的清洗模板" },
        { value: "video", label: "视频", icon: "🎥", description: "处理视频数据的清洗模板" },
        { value: "audio", label: "音频", icon: "🎵", description: "处理音频数据的清洗模板" },
        { value: "image-to-text", label: "图片转文本", icon: "🔄", description: "图像识别转文本的处理模板" },
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
        if (currentStep < 1) {
            setCurrentStep(currentStep + 1)
        }
    }

    const handlePrev = () => {
        if (currentStep > 0) {
            setCurrentStep(currentStep - 1)
        }
    }

    const handleSave = () => {
        const template = {
            ...templateConfig,
            operators: selectedOperators,
            createdAt: new Date().toISOString(),
        }
        onSave(template)
    }

    const canProceed = () => {
        switch (currentStep) {
            case 0:
                return templateConfig.name && templateConfig.description && templateConfig.type
            case 1:
                return selectedOperators.length > 0
            default:
                return false
        }
    }

    const renderStepContent = () => {
        switch (currentStep) {
            case 0:
                return (
                    <Form layout="vertical">
                        <Form.Item label="模板名称 *" required>
                            <Input
                                value={templateConfig.name}
                                onChange={(e) => setTemplateConfig({ ...templateConfig, name: e.target.value })}
                                placeholder="输入模板名称"
                                size="large"
                            />
                        </Form.Item>
                        <Form.Item label="模板描述 *" required>
                            <TextArea
                                value={templateConfig.description}
                                onChange={(e) => setTemplateConfig({ ...templateConfig, description: e.target.value })}
                                placeholder="描述模板的用途和特点"
                                rows={4}
                            />
                        </Form.Item>
                        <div />
                        <div style={{ fontWeight: 600, fontSize: 16, marginBottom: 16 }}>模板类型</div>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
                            {templateTypes.map((type) => (
                                <Card
                                    key={type.value}
                                    hoverable
                                    style={{
                                        borderColor: templateConfig.type === type.value ? "#1677ff" : undefined,
                                        background: templateConfig.type === type.value ? "#e6f7ff" : undefined,
                                        cursor: "pointer",
                                    }}
                                    onClick={() => setTemplateConfig({ ...templateConfig, type: type.value })}
                                >
                                    <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
                                        <span style={{ fontSize: 24 }}>{type.icon}</span>
                                        <span style={{ fontWeight: 500 }}>{type.label}</span>
                                        {templateConfig.type === type.value && <CheckCircleOutlined style={{ color: "#1677ff", fontSize: 18 }} />}
                                    </div>
                                    <div style={{ color: "#888", fontSize: 13 }}>{type.description}</div>
                                </Card>
                            ))}
                        </div>
                    </Form>
                )
            case 1:
                return (
                    <div>
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                            <div>
                                <span style={{ fontWeight: 600, fontSize: 18 }}>算子编排</span>
                                <span style={{ color: "#888", marginLeft: 8 }}>
                                    为 {templateTypes.find((t) => t.value === templateConfig.type)?.label} 类型模板选择和配置算子
                                </span>
                            </div>
                            <Badge
                                style={{
                                    background: "#e6f7ff",
                                    color: "#1677ff",
                                    border: "1px solid #91d5ff",
                                    fontWeight: 500,
                                    fontSize: 14,
                                    padding: "4px 12px",
                                }}
                            >
                                {templateTypes.find((t) => t.value === templateConfig.type)?.icon}{" "}
                                {templateTypes.find((t) => t.value === templateConfig.type)?.label}
                            </Badge>
                        </div>
                        <OperatorOrchestrationPage handleAdd={addOperator} handleRemove={removeOperator} />
                    </div>
                )
            default:
                return null
        }
    }

    return (
        <div >
            {/* Header */}
            <div className="flex mb-6 items-center gap-6 w-full">
                <Button
                    type="text"
                    size="small"
                    onClick={() => navigate('/data/cleansing')}
                    icon={<ArrowRightOutlined style={{ transform: "rotate(180deg)" }} />}
                />
                <div>
                    <div style={{ fontWeight: 700, fontSize: 24 }}>创建清洗模板</div>
                    <div style={{ color: "#888", fontSize: 14, marginTop: 4 }}>创建可复用的数据清洗流程模板</div>
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

            {/* Progress Steps */}
            <Card>

                {renderStepContent()}

                <div className="w-full mt-8 flex justify-end border-t pt-6 gap-4">
                    <Button onClick={() => navigate('/data/cleansing')}>取消</Button>
                    {currentStep > 0 && (
                        <Button onClick={handlePrev} >
                            上一步
                        </Button>
                    )}
                    {currentStep === 1 ? (
                        <Button
                            type="primary"
                            onClick={handleSave}
                            disabled={!canProceed()}
                        >
                            创建模板
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
        </div>
    )
}