import { Handle, Position } from "@xyflow/react";

import { Button, Card } from "antd";
import {
  Settings,
  Database,
  Trash2,
  Copy,
  ChevronDown,
  MessageSquare,
  Brain,
  Cpu,
} from "lucide-react";
import { useState } from "react";

const CustomNode = ({ data, selected }: { data: any; selected: boolean }) => {
  const [isHovered, setIsHovered] = useState(false);

  const getNodeIcon = (type: string) => {
    switch (type) {
      case "knowledge-search":
        return <Database className="w-4 h-4 text-blue-600" />;
      case "ai-dialogue":
        return <MessageSquare className="w-4 h-4 text-blue-600" />;
      case "data-processing":
        return <Cpu className="w-4 h-4 text-blue-600" />;
      default:
        return <Brain className="w-4 h-4 text-blue-600" />;
    }
  };

  return (
    <div
      className="relative"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Left side handles - inputs */}
      <Handle
        type="target"
        position={Position.Left}
        id="left-input"
        className="w-3 h-3 bg-green-500 border-2 border-white shadow-md hover:bg-green-600 transition-all duration-200 hover:scale-110"
        style={{ left: -6, top: "50%" }}
      />

      {/* Right side handles - outputs */}
      <Handle
        type="source"
        position={Position.Right}
        id="right-output"
        className="w-3 h-3 bg-blue-500 border-2 border-white shadow-md hover:bg-blue-600 transition-all duration-200 hover:scale-110"
        style={{ right: -6, top: "50%" }}
      />

      <Card
        className={`w-80 transition-all duration-200 ${selected
            ? "ring-2 ring-blue-500 shadow-lg"
            : "shadow-md hover:shadow-lg"
          }`}
        styles={{ body: { padding: 0 } }}
      >
        <div className="pb-3 bg-blue-50 border-b px-4 pt-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                {getNodeIcon(data.type)}
              </div>
              <div>
                <div className="font-semibold text-gray-900">{data.name}</div>
                <div className="text-sm text-gray-600">{data.description}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                type="text"
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  data.onDuplicate?.(data.id);
                }}
                className="h-8 w-8 p-0 text-gray-500 hover:text-gray-700"
                icon={<Copy className="w-4 h-4" />}
              />
              <Button
                type="text"
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  data.onDelete?.(data.id);
                }}
                className="h-8 w-8 p-0 text-gray-500 hover:text-red-600"
                icon={<Trash2 className="w-4 h-4" />}
              />
            </div>
          </div>
        </div>
        <div className="p-4 space-y-4">
          {/* Input Section */}
          <div>
            <div className="font-medium text-gray-900 mb-3 flex items-center gap-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              输入
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">AI 模型</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">手动选择</span>
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                </div>
              </div>
              <Button type="primary" className="w-full">
                <Settings className="w-4 h-4 mr-2" />
                装载
              </Button>
            </div>
          </div>

          {/* Parameters Table */}
          <div>
            <div className="font-medium text-gray-900 mb-3">搜索参数设置</div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="grid grid-cols-5 gap-2 text-xs font-medium text-gray-600 mb-2">
                <div>查询方式</div>
                <div>可用上限</div>
                <div>查询参数</div>
                <div>检索数量</div>
                <div>问题优化</div>
              </div>
              <div className="grid grid-cols-5 gap-2 text-xs text-gray-700">
                <div>含义文档</div>
                <div>5000</div>
                <div>0.4</div>
                <div className="text-red-500">✕</div>
                <div>Qwen-max</div>
              </div>
            </div>
          </div>

          {/* Output Section */}
          <div>
            <div className="font-medium text-gray-900 mb-2 flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              输出
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">知识库内容</span>
              <span className="text-gray-500">知识库搜索</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default CustomNode;
