import { useState } from "react";
import { Card, Table, Badge, Button } from "antd";
import { EditOutlined, DeleteOutlined } from "@ant-design/icons";
import { Plus, FileText } from "lucide-react";
import type { Template } from "@/pages/SynthesisTask/synthesis";
import { useNavigate } from "react-router";
import { mockTemplates } from "@/mock/synthesis";
import { SearchControls } from "@/components/SearchControls";

export default function InstructionTemplateTab() {
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState("");

  const [templates, setTemplates] = useState<Template[]>(mockTemplates);
  const [filterTemplateType, setFilterTemplateType] = useState("all");

  // 过滤模板
  const filteredTemplates = templates.filter((template) => {
    const matchesSearch =
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType =
      filterTemplateType === "all" || template.type === filterTemplateType;
    return matchesSearch && matchesType;
  });

  const getQualityColor = (quality: number) => {
    if (quality >= 90) return "text-green-600 bg-green-50 border-green-200";
    if (quality >= 80) return "text-blue-600 bg-blue-50 border-blue-200";
    if (quality >= 70) return "text-yellow-600 bg-yellow-50 border-yellow-200";
    return "text-red-600 bg-red-50 border-red-200";
  };

  // 模板表格列
  const templateColumns = [
    {
      title: "模板名称",
      dataIndex: "name",
      key: "name",
      fixed: "left",
      render: (text: string, template: Template) => (
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-purple-500 rounded-lg flex items-center justify-center shadow-sm">
            <FileText className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="font-medium text-gray-900 text-sm">
              {template.name}
            </div>
            <div className="text-xs text-gray-500 line-clamp-1">
              {template.description}
            </div>
          </div>
        </div>
      ),
    },
    {
      title: "类型",
      dataIndex: "type",
      key: "type",
      render: (type: string) => (
        <Badge className="text-xs">
          {type === "preset" ? "预置" : "自定义"}
        </Badge>
      ),
    },
    {
      title: "分类",
      dataIndex: "category",
      key: "category",
      render: (category: string) => (
        <Badge className="bg-purple-50 text-purple-700 border-purple-200 text-xs">
          {category}
        </Badge>
      ),
    },
    {
      title: "变量数量",
      dataIndex: "variables",
      key: "variables",
      render: (variables: string[]) => (
        <div className="text-sm font-medium text-gray-900">
          {variables.length}
        </div>
      ),
    },
    {
      title: "使用次数",
      dataIndex: "usageCount",
      key: "usageCount",
      render: (usageCount: number) => (
        <div className="text-sm font-medium text-gray-900">{usageCount}</div>
      ),
    },
    {
      title: "质量评分",
      dataIndex: "quality",
      key: "quality",
      render: (quality: number) => (quality ? `${quality}%` : "-"),
    },
    {
      title: "最后使用",
      dataIndex: "lastUsed",
      key: "lastUsed",
      render: (lastUsed: string) => (
        <div className="text-sm text-gray-600">{lastUsed || "-"}</div>
      ),
    },
    {
      title: "操作",
      key: "actions",
      fixed: "right",
      render: (_: any, template: Template) => (
        <div className="flex items-center justify-center">
          <Button type="text">
            <EditOutlined />
          </Button>
          <Button type="text" danger>
            <DeleteOutlined />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <SearchControls
        searchTerm={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="搜索模板名称或描述..."
        filters={[
          {
            key: "type",
            label: "类型",
            options: [
              { label: "全部类型", value: "all" },
              { label: "预置模板", value: "preset" },
              { label: "自定义模板", value: "custom" },
            ],
          },
        ]}
        selectedFilters={{ type: [filterTemplateType] }}
        onFiltersChange={(filters) => {
          setFilterTemplateType(filters.type?.[0] || "all");
        }}
        showFilters
        showViewToggle={false}
      />

      {/* 模板表格 */}
      <Card className="shadow-sm border-0 bg-white">
        <Table
          scroll={{ x: "max-content" }}
          columns={templateColumns}
          dataSource={filteredTemplates}
          rowKey="id"
          pagination={false}
          locale={{
            emptyText: (
              <div className="text-center py-12">
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <h3 className="text-base font-semibold text-gray-900 mb-2">
                  暂无指令模板
                </h3>
                <p className="text-gray-500 mb-4 text-sm">
                  {searchQuery
                    ? "没有找到匹配的模板"
                    : "开始创建您的第一个指令模板"}
                </p>
                {!searchQuery && (
                  <Button
                    onClick={() =>
                      navigate("/data/synthesis/task/create-template")
                    }
                    className="px-6 py-2 text-sm font-semibold bg-purple-600 hover:bg-purple-700 shadow-lg"
                  >
                    <Plus className="w-3 h-3 mr-1" />
                    创建模板
                  </Button>
                )}
              </div>
            ),
          }}
        />
      </Card>
    </div>
  );
}
