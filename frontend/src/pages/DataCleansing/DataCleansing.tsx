"use client"

import { useState } from "react"
import { Card, Tabs, Table, Progress, Badge, Button, Dropdown, Menu } from "antd"
import { PlusOutlined, PlayCircleOutlined, PauseCircleOutlined, EyeOutlined, SettingOutlined, DownloadOutlined, DeleteOutlined, EditOutlined, ShareAltOutlined, DatabaseOutlined, FileTextOutlined, ClockCircleOutlined, CheckCircleOutlined, AlertOutlined, AppstoreOutlined, FileOutlined } from "@ant-design/icons"
import { SearchControls } from "@/components/SearchControls"
import CardView from "@/components/CardView"
import { useNavigate } from "react-router"

// ====== Mocked Data Extracted Outside Component ======
const MOCK_TASKS = [
    {
        id: 1,
        name: "肺癌WSI图像清洗",
        description: "肺癌WSI病理图像数据集的标准化清洗任务",
        dataset: "肺癌WSI病理图像数据集",
        newDatasetName: "肺癌WSI图像_清洗后",
        template: "医学影像标准清洗",
        batchSize: 100,
        status: "运行中",
        progress: 60,
        startTime: "2024-01-20 09:30:15",
        estimatedTime: "2小时",
        totalFiles: 1250,
        processedFiles: 750,
        operators: ["格式转换", "噪声去除", "尺寸标准化", "质量检查"],
    },
    {
        id: 2,
        name: "病理WSI图像处理",
        description: "WSI病理切片图像的专业清洗流程",
        dataset: "WSI切片数据集",
        newDatasetName: "WSI切片_清洗后",
        template: "病理WSI图像处理",
        batchSize: 100,
        status: "已完成",
        progress: 100,
        startTime: "2024-01-18 14:10:00",
        estimatedTime: "1小时30分",
        totalFiles: 800,
        processedFiles: 800,
        operators: ["格式转换", "色彩校正", "分辨率调整", "组织区域提取"],
    },
    {
        id: 3,
        name: "医学文本清洗",
        description: "医学文本数据的标准化清洗流程",
        dataset: "医学文本数据集",
        newDatasetName: "医学文本_清洗后",
        template: "医学文本清洗",
        batchSize: 200,
        status: "队列中",
        progress: 0,
        startTime: "待开始",
        estimatedTime: "预计2小时",
        totalFiles: 1000,
        processedFiles: 0,
        operators: ["编码转换", "格式统一", "敏感信息脱敏", "质量过滤"],
    },
]

const MOCK_TEMPLATES = [
    {
        id: "medical-image",
        name: "医学影像标准清洗",
        description: "专用于医学影像的标准化清洗流程，包含格式转换、质量检查等步骤",
        operators: ["DICOM解析", "格式标准化", "窗宽窗位调整", "噪声去除", "质量检查"],
        category: "医学影像",
        usage: 156,
        color: "blue",
    },
    {
        id: "pathology-wsi",
        name: "病理WSI图像处理",
        description: "WSI病理切片图像的专业清洗流程，优化病理诊断数据质量",
        operators: ["格式转换", "色彩校正", "分辨率调整", "组织区域提取"],
        category: "病理学",
        usage: 89,
        color: "green",
    },
    {
        id: "text-cleaning",
        name: "医学文本清洗",
        description: "医学文本数据的标准化清洗流程，确保文本数据的一致性和质量",
        operators: ["编码转换", "格式统一", "敏感信息脱敏", "质量过滤"],
        category: "文本处理",
        usage: 234,
        color: "purple",
    },
    {
        id: "general-image",
        name: "通用图像清洗",
        description: "适用于各类图像数据的通用清洗流程，提供基础的图像处理功能",
        operators: ["质量检查", "重复检测", "异常过滤", "格式转换"],
        category: "通用",
        usage: 445,
        color: "orange",
    },
    {
        id: "audio-processing",
        name: "音频数据清洗",
        description: "专门针对医学音频数据的清洗和预处理流程",
        operators: ["噪声去除", "格式转换", "音量标准化", "质量检测"],
        category: "音频处理",
        usage: 67,
        color: "pink",
    },
    {
        id: "multimodal-clean",
        name: "多模态数据清洗",
        description: "处理包含多种数据类型的综合清洗流程",
        operators: ["数据分类", "格式统一", "质量检查", "关联验证"],
        category: "多模态",
        usage: 123,
        color: "geekblue",
    },
]
// ====== End Mocked Data ======

export default function DataProcessingPage() {
    const navigate = useNavigate();
    const [currentView, setCurrentView] = useState<"tasks" | "templates">("tasks")
    const [selectedTask, setSelectedTask] = useState<any>(null)
    const [selectedTemplate, setSelectedTemplate] = useState<any>(null)

    const [searchTerm, setSearchTerm] = useState("")
    const [filterType, setFilterType] = useState("all")
    const [filterStatus, setFilterStatus] = useState("all")
    const [filterCategory, setFilterCategory] = useState("all")
    const [viewMode, setViewMode] = useState<"card" | "list">("card")

    // Use state to initiate with mock data
    const [cleaningTasks, setCleaningTasks] = useState(MOCK_TASKS)
    const [templateList, setTemplateList] = useState(MOCK_TEMPLATES)

    const getStatusBadge = (status: string) => {
        const statusConfig = {
            运行中: { color: "blue", icon: <PlayCircleOutlined /> },
            已完成: { color: "green", icon: <CheckCircleOutlined /> },
            队列中: { color: "gold", icon: <ClockCircleOutlined /> },
            已暂停: { color: "default", icon: <PauseCircleOutlined /> },
            失败: { color: "red", icon: <AlertOutlined /> },
        }
        return statusConfig[status as keyof typeof statusConfig] || statusConfig.队列中
    }

    const handleCreateTask = (taskData: any) => {
        const newTask = {
            id: cleaningTasks.length + 1,
            name: taskData.name,
            description: taskData.description,
            dataset: taskData.datasetId,
            newDatasetName: taskData.newDatasetName,
            template: "自定义流程",
            batchSize: taskData.batchSize,
            status: "队列中",
            progress: 0,
            startTime: "待开始",
            estimatedTime: "预计2小时",
            totalFiles: 1000,
            processedFiles: 0,
            operators: taskData.operators.map((op: any) => op.name),
        }
        setCleaningTasks([...cleaningTasks, newTask])
        setCurrentView("list")
    }

    const handleViewTask = (task: any) => {
        setSelectedTask(task)
        navigate('/data/cleansing/task-detail/' + task.id)
    }

    const handleCreateTemplate = (templateData: any) => {
        // 在实际应用中，这里会发送API请求保存模板
        setTemplateList([...templateList, templateData])
    }

    const handleViewTemplate = (template: any) => {
        setSelectedTemplate(template)
        navigate('/data/cleansing/template-create')
    }

    if (currentView === "create") {
        navigate('/data/cleansing/task-create')
    }

    if (currentView === "create-template") {
        navigate('/data/cleansing/template-create')
    }

    if (currentView === "detail" && selectedTask) {
        navigate(`/data/cleansing/task-detail/${selectedTask.id}`)
    }

    if (currentView === "template-detail" && selectedTemplate) {
        navigate(`/data/cleansing/template-detail/${selectedTemplate.id}`)
    }

    const taskColumns = [
        {
            title: "任务名称",
            dataIndex: "name",
            key: "name",
            render: (text: string, record: any) => <a onClick={() => handleViewTask(record)}>{text}</a>,
        },
        {
            title: "数据集",
            dataIndex: "dataset",
            key: "dataset",
        },
        {
            title: "状态",
            dataIndex: "status",
            key: "status",
            render: (status: string) => {
                const statusConfig = getStatusBadge(status)
                return <Badge color={statusConfig.color} text={status} />
            },
        },
        {
            title: "开始时间",
            dataIndex: "startTime",
            key: "startTime",
        },
        {
            title: "进度",
            dataIndex: "progress",
            key: "progress",
            render: (progress: number) => <Progress percent={progress} size="small" />,
        },
        {
            title: "操作",
            key: "action",
            render: (text: string, record: any) => (
                <div style={{ display: "flex", gap: 8 }}>
                    <Button type="text" icon={<EyeOutlined />} onClick={() => handleViewTask(record)} />
                    {record.status === "运行中" ? (
                        <Button type="text" icon={<PauseCircleOutlined />} />
                    ) : record.status === "队列中" ? (
                        <Button type="text" icon={<PlayCircleOutlined />} />
                    ) : null}
                    <Dropdown
                        overlay={
                            <Menu>
                                <Menu.Item key="download" icon={<DownloadOutlined />}>下载结果</Menu.Item>
                                <Menu.Item key="delete" icon={<DeleteOutlined />} danger>删除任务</Menu.Item>
                            </Menu>
                        }
                        trigger={['click']}
                    >
                        <Button type="text" icon={<SettingOutlined />} />
                    </Dropdown>
                </div>
            ),
        },
    ]

    const renderTaskList = (
        <div style={{ marginBottom: 24 }}>
            {/* Search and Filters */}
            <SearchControls
                searchTerm={searchTerm}
                onSearchChange={setSearchTerm}
                searchPlaceholder="搜索任务名称、描述"
                filters={[
                    {
                        key: "type",
                        label: "类型",
                        options: [
                            { label: "所有类型", value: "all" },
                            { label: "图像", value: "image" },
                            { label: "文本", value: "text" },
                            { label: "音频", value: "audio" },
                            { label: "视频", value: "video" },
                            { label: "多模态", value: "multimodal" },
                        ],
                    },
                    {
                        key: "status",
                        label: "状态",
                        options: [
                            { label: "所有状态", value: "all" },
                            { label: "活跃", value: "active" },
                            { label: "处理中", value: "processing" },
                            { label: "已归档", value: "archived" },
                        ],
                    },
                ]}
                selectedFilters={{
                    type: filterType !== "all" ? [filterType] : [],
                    status: filterStatus !== "all" ? [filterStatus] : [],
                }}
                onFiltersChange={(filters) => {
                    setFilterType(filters.type?.[0] || "all")
                    setFilterStatus(filters.status?.[0] || "all")
                }}
                viewMode={viewMode}
                onViewModeChange={setViewMode}
                showViewToggle={true}
            />
            {/* Task List */}
            {viewMode === "card" ? (
                <CardView
                    data={cleaningTasks.map(task => ({
                        id: task.id,
                        name: task.name,
                        type: task.template,
                        icon: <DatabaseOutlined style={{ color: "#1677ff" }} />,
                        iconColor: "bg-blue-100",
                        status: {
                            label: task.status,
                            color: getStatusBadge(task.status).color,
                        },
                        description: task.description || "",
                        tags: task.operators,
                        statistics: [
                            { label: "进度", value: `${task.progress}%` },
                            { label: "已处理", value: task.processedFiles },
                            { label: "总数", value: task.totalFiles },
                        ],
                        lastModified: task.startTime,
                    }))}
                    operations={[
                        {
                            key: "view",
                            label: "查看",
                            icon: <EyeOutlined />,
                            onClick: (item) => handleViewTask(cleaningTasks.find(t => t.id === item.id)),
                        },
                        {
                            key: "download",
                            label: "下载",
                            icon: <DownloadOutlined />,
                            onClick: (item) => { }, // implement download logic
                        },
                        {
                            key: "delete",
                            label: "删除",
                            icon: <DeleteOutlined />,
                            onClick: (item) => { }, // implement delete logic
                        },
                    ]}
                    onView={(item) => handleViewTask(cleaningTasks.find(t => t.id === item.id))}
                />
            ) : (
                <Table columns={taskColumns} dataSource={cleaningTasks} rowKey="id" />
            )}
        </div>
    )

    const renderTemplateManagement = (
        <div>
            <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 24 }}>
                <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => navigate('/data/cleansing/template-create')}
                >
                    创建模板
                </Button>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 24 }}>
                {templateList.map((template) => (
                    <Card key={template.id} hoverable>
                        <div style={{ marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                            <span style={{ fontWeight: 600, fontSize: 16 }}>{template.name}</span>
                            <Badge color={template.color} text={template.category} />
                            <span style={{ fontSize: 12, color: "#888" }}><ShareAltOutlined /> 使用 {template.usage} 次</span>
                        </div>
                        <div style={{ fontSize: 13, color: "#666", marginBottom: 12 }}>{template.description}</div>
                        <div style={{ marginBottom: 12 }}>
                            <span style={{ fontSize: 12, color: "#888" }}>包含算子：</span>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 4 }}>
                                {template.operators.map((operator: string, idx: number) => (
                                    <Badge key={idx} color="blue" text={operator} />
                                ))}
                            </div>
                        </div>
                        <Button block icon={<AppstoreOutlined />}>使用模板</Button>
                        <Dropdown
                            overlay={
                                <Menu>
                                    <Menu.Item key="view" icon={<EyeOutlined />} onClick={() => handleViewTemplate(template)}>查看详情</Menu.Item>
                                    <Menu.Item key="edit" icon={<EditOutlined />}>编辑模板</Menu.Item>
                                    <Menu.Item key="delete" icon={<DeleteOutlined />} danger>删除模板</Menu.Item>
                                </Menu>
                            }
                            trigger={['click']}
                        >
                            <Button type="text" icon={<SettingOutlined />} style={{ float: "right", marginTop: 8 }} />
                        </Dropdown>
                    </Card>
                ))}
            </div>
        </div>
    )

    return (
        <div style={{ minHeight: "100vh" }}>
            <div style={{ marginBottom: 24 }}>
                {/* Header */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <h1 style={{ fontWeight: 700, fontSize: 22 }}>数据清洗</h1>
                    <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={() => navigate('/data/cleansing/task-create')}
                    >
                        创建清洗任务
                    </Button>
                </div>
            </div>

            <Tabs
                activeKey={currentView}
                onChange={(key) => setCurrentView(key as any)}
                items={[
                    {
                        key: "tasks",
                        label: "任务列表",
                        children: renderTaskList,
                    },
                    {
                        key: "templates",
                        label: "模板管理",
                        children: renderTemplateManagement,
                    },
                ]}
            />
        </div>
    )
}
