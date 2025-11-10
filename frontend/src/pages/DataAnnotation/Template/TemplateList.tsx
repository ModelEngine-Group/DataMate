import React, { useState, useEffect } from "react";
import {
    Button,
    Table,
    Space,
    Tag,
    message,
    Input,
    Select,
    Tooltip,
    Popconfirm,
    Card,
} from "antd";
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    EyeOutlined,
    FilterOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import {
    queryAnnotationTemplatesUsingGet,
    deleteAnnotationTemplateByIdUsingDelete,
} from "../annotation.api";
import type { AnnotationTemplate } from "../annotation.model";
import TemplateForm from "./TemplateForm.tsx";
import TemplateDetail from "./TemplateDetail.tsx";

const { Search } = Input;
const { Option } = Select;

const TemplateList: React.FC = () => {
    const [templates, setTemplates] = useState<AnnotationTemplate[]>([]);
    const [loading, setLoading] = useState(false);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [size, setSize] = useState(10);

    // Filters
    const [searchText, setSearchText] = useState("");
    const [categoryFilter, setCategoryFilter] = useState<string | undefined>();
    const [dataTypeFilter, setDataTypeFilter] = useState<string | undefined>();
    const [labelingTypeFilter, setLabelingTypeFilter] = useState<string | undefined>();
    const [builtInFilter, setBuiltInFilter] = useState<boolean | undefined>();

    // Modals
    const [isFormVisible, setIsFormVisible] = useState(false);
    const [isDetailVisible, setIsDetailVisible] = useState(false);
    const [selectedTemplate, setSelectedTemplate] = useState<AnnotationTemplate | undefined>();
    const [formMode, setFormMode] = useState<"create" | "edit">("create");

    useEffect(() => {
        fetchTemplates();
    }, [page, size, categoryFilter, dataTypeFilter, labelingTypeFilter, builtInFilter]);

    const fetchTemplates = async () => {
        setLoading(true);
        try {
            const params: any = {
                page,
                size,
            };

            if (categoryFilter) params.category = categoryFilter;
            if (dataTypeFilter) params.dataType = dataTypeFilter;
            if (labelingTypeFilter) params.labelingType = labelingTypeFilter;
            if (builtInFilter !== undefined) params.builtIn = builtInFilter;

            const response = await queryAnnotationTemplatesUsingGet(params);
            if (response.code === 200 && response.data) {
                setTemplates(response.data.content || []);
                setTotal(response.data.total || 0);
            }
        } catch (error) {
            message.error("获取模板列表失败");
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = () => {
        setFormMode("create");
        setSelectedTemplate(undefined);
        setIsFormVisible(true);
    };

    const handleEdit = (template: AnnotationTemplate) => {
        setFormMode("edit");
        setSelectedTemplate(template);
        setIsFormVisible(true);
    };

    const handleView = (template: AnnotationTemplate) => {
        setSelectedTemplate(template);
        setIsDetailVisible(true);
    };

    const handleDelete = async (templateId: string) => {
        try {
            const response = await deleteAnnotationTemplateByIdUsingDelete(templateId);
            if (response.code === 200) {
                message.success("模板删除成功");
                fetchTemplates();
            } else {
                message.error(response.message || "删除模板失败");
            }
        } catch (error) {
            message.error("删除模板失败");
            console.error(error);
        }
    };

    const handleFormSuccess = () => {
        setIsFormVisible(false);
        fetchTemplates();
    };

    const handleClearFilters = () => {
        setCategoryFilter(undefined);
        setDataTypeFilter(undefined);
        setLabelingTypeFilter(undefined);
        setBuiltInFilter(undefined);
        setSearchText("");
    };

    const getCategoryColor = (category: string) => {
        const colors: Record<string, string> = {
            "computer-vision": "blue",
            "nlp": "green",
            "audio": "purple",
            "quality-control": "orange",
            "custom": "default",
        };
        return colors[category] || "default";
    };

    const columns: ColumnsType<AnnotationTemplate> = [
        {
            title: "模板名称",
            dataIndex: "name",
            key: "name",
            width: 200,
            ellipsis: true,
            filteredValue: searchText ? [searchText] : null,
            onFilter: (value, record) =>
                record.name.toLowerCase().includes(value.toString().toLowerCase()) ||
                (record.description?.toLowerCase().includes(value.toString().toLowerCase()) ?? false),
        },
        {
            title: "描述",
            dataIndex: "description",
            key: "description",
            ellipsis: {
                showTitle: false,
            },
            render: (description: string) => (
                <Tooltip title={description}>
                    <div
                        style={{
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'normal',
                            lineHeight: '1.5em',
                            maxHeight: '3em',
                        }}
                    >
                        {description}
                    </div>
                </Tooltip>
            ),
        },
        {
            title: "数据类型",
            dataIndex: "dataType",
            key: "dataType",
            width: 120,
            render: (dataType: string) => (
                <Tag color="cyan">{dataType}</Tag>
            ),
        },
        {
            title: "标注类型",
            dataIndex: "labelingType",
            key: "labelingType",
            width: 150,
            render: (labelingType: string) => (
                <Tag color="geekblue">{labelingType}</Tag>
            ),
        },
        {
            title: "分类",
            dataIndex: "category",
            key: "category",
            width: 150,
            render: (category: string) => (
                <Tag color={getCategoryColor(category)}>{category}</Tag>
            ),
        },
        {
            title: "类型",
            dataIndex: "builtIn",
            key: "builtIn",
            width: 100,
            render: (builtIn: boolean) => (
                <Tag color={builtIn ? "gold" : "default"}>
                    {builtIn ? "系统内置" : "自定义"}
                </Tag>
            ),
        },
        {
            title: "版本",
            dataIndex: "version",
            key: "version",
            width: 80,
        },
        {
            title: "创建时间",
            dataIndex: "createdAt",
            key: "createdAt",
            width: 180,
            render: (date: string) => new Date(date).toLocaleString(),
        },
        {
            title: "操作",
            key: "action",
            width: 200,
            fixed: "right",
            render: (_, record) => (
                <Space size="small">
                    <Tooltip title="查看详情">
                        <Button
                            type="link"
                            icon={<EyeOutlined />}
                            onClick={() => handleView(record)}
                        />
                    </Tooltip>
                    {!record.builtIn && (
                        <>
                            <Tooltip title="编辑">
                                <Button
                                    type="link"
                                    icon={<EditOutlined />}
                                    onClick={() => handleEdit(record)}
                                />
                            </Tooltip>
                            <Popconfirm
                                title="确定要删除这个模板吗？"
                                onConfirm={() => handleDelete(record.id)}
                                okText="确定"
                                cancelText="取消"
                            >
                                <Tooltip title="删除">
                                    <Button
                                        type="link"
                                        danger
                                        icon={<DeleteOutlined />}
                                    />
                                </Tooltip>
                            </Popconfirm>
                        </>
                    )}
                </Space>
            ),
        },
    ];

    const hasActiveFilters = categoryFilter || dataTypeFilter || labelingTypeFilter || builtInFilter !== undefined;

    return (
        <div className="flex flex-col gap-4">
            {/* Search, Filters and Buttons in one row */}
            <div className="flex items-center justify-between gap-2">
                {/* Left side: Search and Filters */}
                <div className="flex items-center gap-2 flex-wrap">
                    <Search
                        placeholder="搜索模板..."
                        allowClear
                        style={{ width: 300 }}
                        value={searchText}
                        onChange={(e) => setSearchText(e.target.value)}
                    />

                    <Select
                        placeholder="分类"
                        allowClear
                        style={{ width: 140 }}
                        value={categoryFilter}
                        onChange={setCategoryFilter}
                    >
                        <Option value="computer-vision">计算机视觉</Option>
                        <Option value="nlp">自然语言处理</Option>
                        <Option value="audio">音频</Option>
                        <Option value="quality-control">质量控制</Option>
                        <Option value="custom">自定义</Option>
                    </Select>

                    <Select
                        placeholder="数据类型"
                        allowClear
                        style={{ width: 120 }}
                        value={dataTypeFilter}
                        onChange={setDataTypeFilter}
                    >
                        <Option value="image">图像</Option>
                        <Option value="text">文本</Option>
                        <Option value="audio">音频</Option>
                        <Option value="video">视频</Option>
                    </Select>

                    <Select
                        placeholder="标注类型"
                        allowClear
                        style={{ width: 140 }}
                        value={labelingTypeFilter}
                        onChange={setLabelingTypeFilter}
                    >
                        <Option value="classification">分类</Option>
                        <Option value="object-detection">目标检测</Option>
                        <Option value="segmentation">分割</Option>
                        <Option value="ner">命名实体识别</Option>
                    </Select>

                    <Select
                        placeholder="模板类型"
                        allowClear
                        style={{ width: 120 }}
                        value={builtInFilter}
                        onChange={setBuiltInFilter}
                    >
                        <Option value={true}>系统内置</Option>
                        <Option value={false}>自定义</Option>
                    </Select>

                    {hasActiveFilters && (
                        <Button icon={<FilterOutlined />} onClick={handleClearFilters}>
                            清空筛选
                        </Button>
                    )}
                </div>

                {/* Right side: Create button */}
                <div className="flex items-center gap-2">
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
                        创建模板
                    </Button>
                </div>
            </div>

            <Card>
                <Table
                    columns={columns}
                    dataSource={templates}
                    rowKey="id"
                    loading={loading}
                    pagination={{
                        current: page,
                        pageSize: size,
                        total: total,
                        showSizeChanger: true,
                        showTotal: (total) => `共 ${total} 个模板`,
                        onChange: (page, pageSize) => {
                            setPage(page);
                            setSize(pageSize);
                        },
                    }}
                    scroll={{ x: 1400, y: "calc(100vh - 24rem)" }}
                />
            </Card>

            <TemplateForm
                visible={isFormVisible}
                mode={formMode}
                template={selectedTemplate}
                onSuccess={handleFormSuccess}
                onCancel={() => setIsFormVisible(false)}
            />

            <TemplateDetail
                visible={isDetailVisible}
                template={selectedTemplate}
                onClose={() => setIsDetailVisible(false)}
            />
        </div>
    );
};

export default TemplateList;
export { TemplateList };
