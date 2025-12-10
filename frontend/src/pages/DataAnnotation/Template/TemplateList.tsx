import React, { useState } from "react";
import {
    Button,
    Table,
    Space,
    Tag,
    message,
    Tooltip,
    Popconfirm,
    Card,
} from "antd";
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    EyeOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import {
    queryAnnotationTemplatesUsingGet,
    deleteAnnotationTemplateByIdUsingDelete,
} from "../annotation.api";
import type { AnnotationTemplate } from "../annotation.model";
import TemplateForm from "./TemplateForm.tsx";
import TemplateDetail from "./TemplateDetail.tsx";
import {SearchControls} from "@/components/SearchControls.tsx";
import useFetchData from "@/hooks/useFetchData.ts";
import {
  AnnotationTypeMap,
  ClassificationMap,
  DataTypeMap,
  TemplateTypeMap
} from "@/pages/DataAnnotation/annotation.const.tsx";

const TemplateList: React.FC = () => {
    const filterOptions = [
      {
        key: "category",
        label: "分类",
        options: [...Object.values(ClassificationMap)],
      },
      {
        key: "dataType",
        label: "数据类型",
        options: [...Object.values(DataTypeMap)],
      },
      {
        key: "labelingType",
        label: "标注类型",
        options: [...Object.values(AnnotationTypeMap)],
      },
      {
        key: "builtIn",
        label: "模板类型",
        options: [...Object.values(TemplateTypeMap)],
      },
    ];

    // Modals
    const [isFormVisible, setIsFormVisible] = useState(false);
    const [isDetailVisible, setIsDetailVisible] = useState(false);
    const [selectedTemplate, setSelectedTemplate] = useState<AnnotationTemplate | undefined>();
    const [formMode, setFormMode] = useState<"create" | "edit">("create");

    const {
      loading,
      tableData,
      pagination,
      searchParams,
      setSearchParams,
      fetchData,
      handleFiltersChange,
      handleKeywordChange,
    } = useFetchData(queryAnnotationTemplatesUsingGet, undefined, undefined, undefined, undefined, 0);

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
                fetchData();
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
        fetchData();
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

    return (
        <div className="flex flex-col gap-4">
            {/* Search, Filters and Buttons in one row */}
            <div className="flex items-center justify-between gap-2">
                {/* Left side: Search and Filters */}
                <div className="flex items-center gap-2 flex-wrap">
                    <SearchControls
                      searchTerm={searchParams.keyword}
                      onSearchChange={handleKeywordChange}
                      searchPlaceholder="搜索任务名称、描述"
                      filters={filterOptions}
                      onFiltersChange={handleFiltersChange}
                      showViewToggle={true}
                      onReload={fetchData}
                      onClearFilters={() => setSearchParams({ ...searchParams, filter: {} })}
                    />
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
                    dataSource={tableData}
                    rowKey="id"
                    loading={loading}
                    pagination={pagination}
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
