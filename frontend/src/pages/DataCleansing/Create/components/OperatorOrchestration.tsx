import React, { useState } from "react";
import { Card, Input, Tag, Select } from "antd";
import {
  SettingOutlined,
  DeleteOutlined,
  ShareAltOutlined,
} from "@ant-design/icons";

interface OperatorConfig {
  id: string;
  name: string;
  category: string;
  icon: React.ReactNode;
  params: Record<string, any>;
  tags: string[];
  description: string;
}

interface OperatorFlowProps {
  operators: OperatorConfig[];
  OPERATOR_CATEGORIES: any;
  selectedOperator: string | null;
  setSelectedOperator: (id: string | null) => void;
  removeOperator: (id: string) => void;
  setOperators: (operators: OperatorConfig[]) => void;
}

const OperatorFlow: React.FC<OperatorFlowProps> = ({
  operators,
  OPERATOR_CATEGORIES,
  selectedOperator,
  setSelectedOperator,
  removeOperator,
  setOperators,
}) => {
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [editingIndex, setEditingIndex] = useState<string | null>(null);

  // 拖拽处理
  const handleDragStart = (e: React.DragEvent, index: number) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  };
  const handleDrop = (e: React.DragEvent, dropIndex: number) => {
    e.preventDefault();
    if (draggedIndex === null) return;
    const newOperators = [...operators];
    const draggedOperator = newOperators[draggedIndex];
    newOperators.splice(draggedIndex, 1);
    newOperators.splice(dropIndex, 0, draggedOperator);
    setOperators(newOperators);
    setDraggedIndex(null);
  };

  return (
    <div className="w-1/2 flex-1 flex flex-col border-x border-gray-200">
      {/* 工具栏 */}
      <div className="px-4 pb-2 border-b border-gray-200">
        <div className="flex justify-between items-start">
          <span className="font-semibold text-base flex items-center gap-2">
            <SettingOutlined />
            算子编排({operators.length})
          </span>
          <Select placeholder="选择模板" className="min-w-64">
            {Object.entries(OPERATOR_CATEGORIES).map(([key, category]: any) => (
              <Select.Option key={key} value={key}>
                <span className="flex items-center gap-1">{category.name}</span>
              </Select.Option>
            ))}
          </Select>
        </div>
      </div>
      {/* 编排区域 */}
      <div className="flex-1 overflow-auto p-4">
        {operators.length === 0 ? (
          <div className="text-center py-16 text-gray-400 border-2 border-dashed border-gray-100 rounded-lg">
            <ShareAltOutlined className="text-5xl mb-4 opacity-50" />
            <div className="text-lg font-medium mb-2">开始构建您的算子流程</div>
            <div className="text-sm">
              从左侧算子库拖拽算子到此处，或点击算子添加
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {operators.map((operator, index) => (
              <Card
                size="small"
                key={operator.id}
                style={
                  selectedOperator === operator.id
                    ? { borderColor: "#1677ff" }
                    : {}
                }
                hoverable
                draggable
                onDragStart={(e) => handleDragStart(e, index)}
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, index)}
                onClick={() => setSelectedOperator(operator.id)}
              >
                <div className="flex items-center gap-1">
                  {/* 可编辑编号 */}
                  {editingIndex === operator.id ? (
                    <Input
                      type="number"
                      min={1}
                      max={operators.length}
                      defaultValue={index + 1}
                      className="w-10 h-6 text-xs text-center"
                      autoFocus
                      onBlur={(e) =>
                        handleIndexChange(operator.id, e.target.value)
                      }
                      onKeyDown={(e) => {
                        if (e.key === "Enter")
                          handleIndexChange(
                            operator.id,
                            (e.target as HTMLInputElement).value
                          );
                        else if (e.key === "Escape") setEditingIndex(null);
                      }}
                      onClick={(e) => e.stopPropagation()}
                    />
                  ) : (
                    <Tag
                      color="default"
                      onClick={(e) => {
                        e.stopPropagation();
                        setEditingIndex(operator.id);
                      }}
                    >
                      {index + 1}
                    </Tag>
                  )}
                  {/* 算子图标和名称 */}
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <span className="font-medium text-sm truncate">
                      {operator.name}
                    </span>
                  </div>
                  {/* 分类标签 */}
                  <Tag color="default">
                    {OPERATOR_CATEGORIES[operator.category].name}
                  </Tag>
                  {/* 参数状态指示 */}
                  {Object.values(operator.params).some(
                    (param: any) =>
                      (param.type === "input" && !param.value) ||
                      (param.type === "checkbox" &&
                        Array.isArray(param.value) &&
                        param.value.length === 0)
                  ) && <Tag color="red">待配置</Tag>}
                  {/* 操作按钮 */}
                  <span
                    className="cursor-pointer text-red-500"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeOperator(operator.id);
                    }}
                  >
                    <DeleteOutlined />
                  </span>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default OperatorFlow;
