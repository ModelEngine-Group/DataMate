import type React from "react";
import { useState, useCallback } from "react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  type Connection,
  type Node,
  type NodeTypes,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { Button, Card, Input, Badge, Typography } from "antd";
import TextArea from "antd/es/input/TextArea";
import {
  Play,
  Save,
  ArrowLeft,
  Database,
  Download,
  Bug,
  Search,
  MessageSquare,
  Cpu,
} from "lucide-react";
import CustomNode from "./components/CustomNode";

const { Title } = Typography;

const nodeTypes: NodeTypes = {
  customNode: CustomNode,
};

interface WorkflowEditorProps {
  onBack: () => void;
  onSave: (workflow: any) => void;
  initialWorkflow?: any;
}

const nodeTypeTemplates = [
  {
    type: "knowledge-search",
    name: "知识库搜索",
    description: "查询、过滤和检索知识库中的文档内容，为AI模型提供上下文信息",
    icon: Database,
    category: "数据源",
    inputs: 1,
    outputs: 1,
  },
  {
    type: "ai-dialogue",
    name: "AI 对话",
    description: "AI 大模型对话",
    icon: MessageSquare,
    category: "AI处理",
    inputs: 1,
    outputs: 1,
  },
  {
    type: "data-processing",
    name: "数据处理",
    description: "对数据进行清洗、转换和处理",
    icon: Cpu,
    category: "数据处理",
    inputs: 1,
    outputs: 1,
  },
  {
    type: "data-output",
    name: "数据输出",
    description: "将处理后的数据输出到指定位置",
    icon: Download,
    category: "数据输出",
    inputs: 1,
    outputs: 0,
  },
];

export default function WorkflowEditor({
  onBack,
  onSave,
  initialWorkflow,
}: WorkflowEditorProps) {
  const [workflow, setWorkflow] = useState({
    id: initialWorkflow?.id || Date.now(),
    name: initialWorkflow?.name || "新建流程",
    description: initialWorkflow?.description || "描述您的数据处理流程",
    category: initialWorkflow?.category || "自定义",
  });

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  const filteredNodeTypes = nodeTypeTemplates.filter(
    (nodeType) =>
      nodeType.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      nodeType.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge(params, eds));
    },
    [setEdges]
  );

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNodeId(node.id);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNodeId(null);
  }, []);

  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData("application/reactflow", nodeType);
    event.dataTransfer.effectAllowed = "move";
  };

  const deleteNode = useCallback(
    (nodeId: string) => {
      setNodes((nds) => nds.filter((node) => node.id !== nodeId));
      setEdges((eds) =>
        eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId)
      );
    },
    [setNodes, setEdges]
  );

  const duplicateNode = useCallback(
    (nodeId: string) => {
      const nodeToDuplicate = nodes.find((node) => node.id === nodeId);
      if (!nodeToDuplicate) return;

      const newNode: Node = {
        ...nodeToDuplicate,
        id: `${nodeToDuplicate.data.type}_${Date.now()}`,
        position: {
          x: nodeToDuplicate.position.x + 50,
          y: nodeToDuplicate.position.y + 50,
        },
        data: {
          ...nodeToDuplicate.data,
          id: `${nodeToDuplicate.data.type}_${Date.now()}`,
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [nodes, setNodes]
  );

  const handleSave = () => {
    const workflowData = {
      ...workflow,
      nodes: nodes.map((node) => ({
        id: node.id,
        type: node.data.type,
        name: node.data.name,
        description: node.data.description,
        position: node.position,
        config: node.data.config || {},
      })),
      connections: edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
      })),
    };
    onSave(workflowData);
  };

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData("application/reactflow");
      if (typeof type === "undefined" || !type) {
        return;
      }

      const position = {
        x: event.clientX - 400, // Adjust for sidebar width
        y: event.clientY - 100, // Adjust for header height
      };

      const nodeTemplate = nodeTypeTemplates.find(
        (template) => template.type === type
      );
      if (!nodeTemplate) return;

      const newNode: Node = {
        id: `${type}_${Date.now()}`,
        type: "customNode",
        position,
        data: {
          id: `${type}_${Date.now()}`,
          type: type,
          name: nodeTemplate.name,
          description: nodeTemplate.description,
          onDelete: deleteNode,
          onDuplicate: duplicateNode,
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [setNodes, deleteNode, duplicateNode]
  );

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              type="text"
              size="small"
              onClick={onBack}
              className="text-gray-600 hover:text-gray-900"
              icon={<ArrowLeft className="w-4 h-4 mr-2" />}
            >
              返回
            </Button>
            <div className="h-6 w-px bg-gray-300" />
            <div>
              <Input
                value={workflow.name}
                onChange={(e) =>
                  setWorkflow((prev) => ({ ...prev, name: e.target.value }))
                }
                className="text-lg font-semibold border-none p-0 h-auto bg-transparent focus-visible:ring-0"
                placeholder="流程名称"
                bordered={false}
              />
              <Input
                value={workflow.description}
                onChange={(e) =>
                  setWorkflow((prev) => ({
                    ...prev,
                    description: e.target.value,
                  }))
                }
                className="text-sm text-gray-600 border-none p-0 h-auto bg-transparent focus-visible:ring-0 mt-1"
                placeholder="流程描述"
                bordered={false}
              />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button
              type="default"
              size="small"
              icon={<Bug className="w-4 h-4 mr-2" />}
            >
              调试
            </Button>
            <Button
              type="default"
              size="small"
              icon={<Play className="w-4 h-4 mr-2" />}
            >
              运行
            </Button>
            <Button
              type="primary"
              onClick={handleSave}
              size="small"
              icon={<Save className="w-4 h-4 mr-2" />}
            >
              保存
            </Button>
          </div>
        </div>
      </div>

      {/* Component Library Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col mt-20">
        <div className="p-4 border-b border-gray-200">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="搜索组件..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <div style={{ flex: 1, overflowY: "auto" }}>
          <div className="p-4 space-y-3">
            {filteredNodeTypes.map((nodeType) => (
              <Card
                key={nodeType.type}
                className="cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow"
                draggable
                onDragStart={(event) => onDragStart(event, nodeType.type)}
                bodyStyle={{ padding: 16 }}
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <nodeType.icon className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900 mb-1">
                      {nodeType.name}
                    </div>
                    <div className="text-sm text-gray-600 leading-relaxed">
                      {nodeType.description}
                    </div>
                    <Badge color="blue" style={{ marginTop: 8, fontSize: 12 }}>
                      {nodeType.category}
                    </Badge>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* Main Canvas */}
      <div className="flex-1 mt-20">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          fitView
          className="bg-gray-50"
          connectionLineStyle={{
            stroke: "#3b82f6",
            strokeWidth: 3,
            strokeDasharray: "5,5",
          }}
          defaultEdgeOptions={{
            type: "smoothstep",
            animated: true,
            style: {
              stroke: "#3b82f6",
              strokeWidth: 3,
              strokeDasharray: "0",
            },
            markerEnd: {
              type: "arrowclosed",
              color: "#3b82f6",
            },
          }}
          isValidConnection={(connection) =>
            connection.source !== connection.target
          }
        >
          <Controls />
          <MiniMap />
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
        </ReactFlow>
      </div>

      {/* Properties Panel */}
      {selectedNodeId && (
        <div className="w-80 bg-white border-l border-gray-200 mt-20">
          <div className="p-4 border-b border-gray-200">
            <Title level={4} style={{ margin: 0 }}>
              节点配置
            </Title>
          </div>
          <div style={{ height: "calc(100% - 56px)", overflowY: "auto" }}>
            <div className="p-4 ">
              {(() => {
                const selectedNode = nodes.find(
                  (node) => node.id === selectedNodeId
                );
                if (!selectedNode) return null;

                return (
                  <>
                    <div>
                      <label
                        htmlFor="node-name"
                        className="block font-medium mb-1"
                      >
                        节点名称
                      </label>
                      <Input
                        id="node-name"
                        value={selectedNode.data.name}
                        onChange={(e) => {
                          setNodes((nds) =>
                            nds.map((node) =>
                              node.id === selectedNode.id
                                ? {
                                    ...node,
                                    data: {
                                      ...node.data,
                                      name: e.target.value,
                                    },
                                  }
                                : node
                            )
                          );
                        }}
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <label
                        htmlFor="node-description"
                        className="block font-medium mb-1"
                      >
                        节点描述
                      </label>
                      <TextArea
                        id="node-description"
                        value={selectedNode.data.description}
                        onChange={(e) => {
                          setNodes((nds) =>
                            nds.map((node) =>
                              node.id === selectedNode.id
                                ? {
                                    ...node,
                                    data: {
                                      ...node.data,
                                      description: e.target.value,
                                    },
                                  }
                                : node
                            )
                          );
                        }}
                        className="mt-1"
                        rows={3}
                      />
                    </div>
                  </>
                );
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
