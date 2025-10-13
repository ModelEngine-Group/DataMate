import React, { useState } from "react";
import { Card, Input, Tag, Select, Button } from "antd";
import {
  SettingOutlined,
  DeleteOutlined,
  ShareAltOutlined,
} from "@ant-design/icons";
import { CleansingTemplate, OperatorI } from "../../cleansing.model";

interface OperatorFlowProps {
  operators: OperatorI[];
  OPERATOR_CATEGORIES: {
    [key: string]: { name: string; icon: React.ReactNode };
  };
  templates: CleansingTemplate[];
  currentTemplate: CleansingTemplate | null;
  setCurrentTemplate: (template: CleansingTemplate | null) => void;
  selectedOperator: string | null;
  setSelectedOperator: (id: string | null) => void;
  removeOperator: (id: string) => void;
  setOperators: (operators: OperatorI[]) => void;
  handleDragStart: (
    e: React.DragEvent,
    operator: OperatorI,
    source: "sort"
  ) => void;
  handleItemDragOver: (e: React.DragEvent, itemId: string) => void;
  handleItemDragLeave: (e: React.DragEvent) => void;
  handleItemDrop: (e: React.DragEvent, index: number) => void;
  handleContainerDragOver: (e: React.DragEvent) => void;
  handleContainerDragLeave: (e: React.DragEvent) => void;
  handleDragEnd: (e: React.DragEvent) => void;
  handleDropToContainer: (e: React.DragEvent) => void;
}

const OperatorFlow: React.FC<OperatorFlowProps> = ({
  OPERATOR_CATEGORIES,
  operators,
  templates,
  currentTemplate,
  selectedOperator,
  setOperators,
  setSelectedOperator,
  removeOperator,
  setCurrentTemplate,
  handleDragStart,
  handleItemDragLeave,
  handleItemDragOver,
  handleItemDrop,
  handleContainerDragLeave,
  handleDropToContainer,
  handleDragEnd,
}) => {
  const [editingIndex, setEditingIndex] = useState<string | null>(null);

  // 添加编号修改处理函数
  const handleIndexChange = (operatorId: string, newIndex: string) => {
    const index = Number.parseInt(newIndex);
    if (isNaN(index) || index < 1 || index > operators.length) {
      return; // 无效输入，不处理
    }

    const currentIndex = operators.findIndex((op) => op.id === operatorId);
    if (currentIndex === -1) return;

    const targetIndex = index - 1; // 转换为0基索引
    if (currentIndex === targetIndex) return; // 位置没有变化

    const newOperators = [...operators];
    const [movedOperator] = newOperators.splice(currentIndex, 1);
    newOperators.splice(targetIndex, 0, movedOperator);

    setOperators(newOperators);
    setEditingIndex(null);
  };

  return (
    <div className="w-1/2 h-screen flex-1 flex flex-col border-x border-gray-200">
      {/* 工具栏 */}
      <div className="px-4 pb-2 border-b border-gray-200">
        <div className="flex justify-between items-start">
          <span className="font-semibold text-base flex items-center gap-2">
            <SettingOutlined />
            算子编排({operators.length}){" "}
            <Button
              type="link"
              size="small"
              onClick={() => {
                setOperators([]);
                setSelectedOperator(null);
              }}
            >
              清空
            </Button>
          </span>
          <Select
            placeholder="选择模板"
            className="min-w-64"
            options={templates}
            value={currentTemplate?.value}
            onChange={(value) =>
              setCurrentTemplate(
                templates.find((t) => t.value === value) || null
              )
            }
          ></Select>
        </div>
      </div>
      {/* 编排区域 */}
      <div
        className="flex-1 overflow-auto p-4 flex flex-col gap-2"
        onDragOver={(e) => e.preventDefault()}
        onDragLeave={handleContainerDragLeave}
        onDrop={handleDropToContainer}
      >
        {operators.length === 0 && (
          <div className="text-center py-16 text-gray-400 border-2 border-dashed border-gray-100 rounded-lg">
            <ShareAltOutlined className="text-5xl mb-4 opacity-50" />
            <div className="text-lg font-medium mb-2">开始构建您的算子流程</div>
            <div className="text-sm">
              从左侧算子库拖拽算子到此处，或点击算子添加
            </div>
          </div>
        )}
        {operators.map((operator, index) => (
          <Card
            size="small"
            key={operator.id}
            style={
              selectedOperator === operator.id ? { borderColor: "#1677ff" } : {}
            }
            hoverable
            draggable
            onDragStart={(e) => handleDragStart(e, operator, "sort")}
            onDragEnd={handleDragEnd}
            onDragOver={(e) => handleItemDragOver(e, operator.id)}
            onDragLeave={handleItemDragLeave}
            onDrop={(e) => handleItemDrop(e, index)}
            onClick={() => setSelectedOperator(operator.id)}
          >
            <div className="flex items-center gap-1">
              {/* 可编辑编号 */}
              <span>⋮⋮</span>
              {editingIndex === operator.id ? (
                <Input
                  type="number"
                  min={1}
                  max={operators.length}
                  defaultValue={index + 1}
                  className="w-10 h-6 text-xs text-center"
                  autoFocus
                  onBlur={(e) => handleIndexChange(operator.id, e.target.value)}
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
                {OPERATOR_CATEGORIES[operator.category]?.name}
              </Tag>
              {/* 参数状态指示 */}
              {Object.values(operator.settings).some(
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
    </div>
  );
};

export default OperatorFlow;
