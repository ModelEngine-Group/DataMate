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
import { TemplateType } from "../annotation.model";
import TemplateForm from "./TemplateForm.tsx";
import TemplateDetail from "./TemplateDetail.tsx";
import {SearchControls} from "@/components/SearchControls.tsx";
import useFetchData from "@/hooks/useFetchData.ts";
import {
    getClassificationMap,
    getDataTypeMap,
    getAnnotationTypeMap,
    getTemplateTypeMap
} from "@/pages/DataAnnotation/annotation.const.tsx";
import { useTranslation } from "react-i18next";

const TemplateList: React.FC = () => {
    const { t } = useTranslation();
    const ClassificationMap = getClassificationMap(t);
    const DataTypeMap = getDataTypeMap(t);
    const AnnotationTypeMap = getAnnotationTypeMap(t);
    const TemplateTypeMap = getTemplateTypeMap(t);

    const filterOptions = [
      {
        key: "category",
        label: t('dataAnnotation.template.filters.category'),
        options: [...Object.values(ClassificationMap)],
      },
      {
        key: "dataType",
        label: t('dataAnnotation.template.filters.dataType'),
        options: [...Object.values(DataTypeMap)],
      },
      {
        key: "labelingType",
        label: t('dataAnnotation.template.filters.labelingType'),
        options: [...Object.values(AnnotationTypeMap)],
      },
      {
        key: "builtIn",
        label: t('dataAnnotation.template.filters.builtIn'),
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
                message.success(t('dataAnnotation.template.messages.deleteSuccess'));
                fetchData();
            } else {
                message.error(response.message || t('dataAnnotation.template.messages.deleteFailed'));
            }
        } catch (error) {
            message.error(t('dataAnnotation.template.messages.deleteFailed'));
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
            title: t('dataAnnotation.template.columns.name'),
            dataIndex: "name",
            key: "name",
            width: 200,
            ellipsis: true,
            onFilter: (value, record) =>
                record.name.toLowerCase().includes(value.toString().toLowerCase()) ||
                (record.description?.toLowerCase().includes(value.toString().toLowerCase()) ?? false),
        },
        {
            title: t('dataAnnotation.template.columns.description'),
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
            title: t('dataAnnotation.template.columns.dataType'),
            dataIndex: "dataType",
            key: "dataType",
            width: 120,
            render: (dataType: string) => (
                <Tag color="cyan">{DataTypeMap[dataType as keyof typeof DataTypeMap]?.label ?? dataType}</Tag>
            ),
        },
        {
            title: t('dataAnnotation.template.columns.labelingType'),
            dataIndex: "labelingType",
            key: "labelingType",
            width: 150,
            render: (labelingType: string) => (
                <Tag color="geekblue">{AnnotationTypeMap[labelingType as keyof typeof AnnotationTypeMap]?.label ?? labelingType}</Tag>
            ),
        },
        {
            title: t('dataAnnotation.template.columns.category'),
            dataIndex: "category",
            key: "category",
            width: 150,
            render: (category: string) => (
                <Tag color={getCategoryColor(category)}>{ClassificationMap[category as keyof typeof ClassificationMap]?.label ?? category}</Tag>
            ),
        },
        {
            title: t('dataAnnotation.template.columns.builtIn'),
            dataIndex: "builtIn",
            key: "builtIn",
            width: 100,
            render: (builtIn: boolean) => (
                <Tag color={builtIn ? "gold" : "default"}>
                    {builtIn ? TemplateTypeMap[TemplateType.SYSTEM]?.label : TemplateTypeMap[TemplateType.CUSTOM]?.label}
                </Tag>
            ),
        },
        {
            title: t('dataAnnotation.template.columns.version'),
            dataIndex: "version",
            key: "version",
            width: 80,
        },
        {
            title: t('dataAnnotation.template.columns.createdAt'),
            dataIndex: "createdAt",
            key: "createdAt",
            width: 180,
            render: (date: string) => new Date(date).toLocaleString(),
        },
        {
            title: t('dataAnnotation.template.columns.actions'),
            key: "action",
            width: 200,
            fixed: "right",
            render: (_, record) => (
                <Space size="small">
                    <Tooltip title={t('dataAnnotation.template.actions.viewDetail')}>
                        <Button
                            type="link"
                            icon={<EyeOutlined />}
                            onClick={() => handleView(record)}
                        />
                    </Tooltip>
                    {!record.builtIn && (
                        <>
                            <Tooltip title={t('dataAnnotation.template.actions.edit')}>
                                <Button
                                    type="link"
                                    icon={<EditOutlined />}
                                    onClick={() => handleEdit(record)}
                                />
                            </Tooltip>
                            <Popconfirm
                                title={t('dataAnnotation.template.messages.deleteConfirm')}
                                onConfirm={() => handleDelete(record.id)}
                                okText={t('dataAnnotation.template.messages.confirmDelete')}
                                cancelText={t('dataAnnotation.template.messages.cancelDelete')}
                            >
                                <Tooltip title={t('dataAnnotation.template.actions.delete')}>
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
                      searchPlaceholder={t('dataAnnotation.template.searchPlaceholder')}
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
                        {t('dataAnnotation.template.create')}
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
