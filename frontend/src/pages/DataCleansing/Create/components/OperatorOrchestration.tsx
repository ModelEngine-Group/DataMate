import React, { useState } from "react";
import { Card, Input, Tag, Select, Button } from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import { CleansingTemplate } from "../../cleansing.model";
import { Workflow } from "lucide-react";
import { OperatorI } from "@/pages/OperatorMarket/operator.model";

interface OperatorFlowProps {
  selectedOperators: OperatorI[];
  configOperator: OperatorI | null;
  templates: CleansingTemplate[];
  currentTemplate: CleansingTemplate | null;
  setCurrentTemplate: (template: CleansingTemplate | null) => void;
  removeOperator: (id: string) => void;
  setSelectedOperators: (operators: OperatorI[]) => void;
  setConfigOperator: (operator: OperatorI | null) => void;
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
  selectedOperators,
  configOperator,
  templates,
  currentTemplate,
  setSelectedOperators,
  setConfigOperator,
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
    if (isNaN(index) || index < 1 || index > selectedOperators.length) {
      return; // 无效输入，不处理
    }

    const currentIndex = selectedOperators.findIndex(
      (op) => op.id === operatorId
    );
    if (currentIndex === -1) return;

    const targetIndex = index - 1; // 转换为0基索引
    if (currentIndex === targetIndex) return; // 位置没有变化

    const newOperators = [...selectedOperators];
    const [movedOperator] = newOperators.splice(currentIndex, 1);
    newOperators.splice(targetIndex, 0, movedOperator);

    setSelectedOperators(newOperators);
    setEditingIndex(null);
  };

  return (
    <div className="w-1/2 h-full min-w-xs flex-1 flex flex-col border-x border-gray-200">
      {/* 工具栏 */}
      <div className="px-4 pb-2 border-b border-gray-200">
        <div className="flex flex-wrap gap-2 justify-between items-start">
          <span className="font-semibold text-base flex items-center gap-2">
            <Workflow className="w-5 h-5" />
            算子编排({selectedOperators.length}){" "}
            <Button
              type="link"
              size="small"
              onClick={() => {
                setConfigOperator(null);
                setSelectedOperators([]);
              }}
              disabled={selectedOperators.length === 0}
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
        className="flex-overflow-auto p-4 gap-2"
        onDragOver={(e) => e.preventDefault()}
        onDragLeave={handleContainerDragLeave}
        onDrop={handleDropToContainer}
      >
        {selectedOperators.map((operator, index) => (
          <Card
            size="small"
            key={operator.id}
            style={
              configOperator?.id === operator.id
                ? { borderColor: "#1677ff" }
                : {}
            }
            hoverable
            draggable
            onDragStart={(e) => handleDragStart(e, operator, "sort")}
            onDragEnd={handleDragEnd}
            onDragOver={(e) => handleItemDragOver(e, operator.id)}
            onDragLeave={handleItemDragLeave}
            onDrop={(e) => handleItemDrop(e, index)}
            onClick={() => setConfigOperator(operator)}
          >
            <div className="flex items-center gap-1">
              {/* 可编辑编号 */}
              <span>⋮⋮</span>
              {editingIndex === operator.id ? (
                <Input
                  type="number"
                  min={1}
                  max={selectedOperators.length}
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
              <Tag color="default">分类</Tag>
              {/* 参数状态指示 */}
              {Object.values(operator.configs).some(
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
        {selectedOperators.length === 0 && (
          <div className="text-center py-16 text-gray-400 border-2 border-dashed border-gray-100 rounded-lg">
            <Workflow className="w-full w-10 h-10 mb-4 opacity-50" />
            <div className="text-lg font-medium mb-2">开始构建您的算子流程</div>
            <div className="text-sm">
              从左侧算子库拖拽算子到此处，或点击算子添加
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OperatorFlow;
