import { useState } from "react";
import { Card, Button, Badge, Input, Checkbox } from "antd";

import {
  File,
  Search,
  CheckCircle,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  HelpCircle,
} from "lucide-react";

interface QAPair {
  id: string;
  question: string;
  answer: string;
  status: "pending" | "approved" | "rejected";
  confidence?: number;
}

interface FileData {
  id: string;
  name: string;
  qaPairs: QAPair[];
}

interface TextAnnotationWorkspaceProps {
  task: any;
  currentFileIndex: number;
  onSaveAndNext: () => void;
  onSkipAndNext: () => void;
}

// 模拟文件数据
const mockFiles: FileData[] = [
  {
    id: "1",
    name: "document_001.txt",
    qaPairs: [
      {
        id: "1",
        question: "什么是人工智能？",
        answer:
          "人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。",
        status: "pending",
        confidence: 0.85,
      },
      {
        id: "2",
        question: "机器学习和深度学习有什么区别？",
        answer:
          "机器学习是人工智能的一个子集，而深度学习是机器学习的一个子集。深度学习使用神经网络来模拟人脑的工作方式。",
        status: "pending",
        confidence: 0.92,
      },
      {
        id: "3",
        question: "什么是神经网络？",
        answer:
          "神经网络是一种受生物神经网络启发的计算模型，由相互连接的节点（神经元）组成，能够学习和识别模式。",
        status: "pending",
        confidence: 0.78,
      },
    ],
  },
  {
    id: "2",
    name: "document_002.txt",
    qaPairs: [
      {
        id: "4",
        question: "什么是自然语言处理？",
        answer:
          "自然语言处理（NLP）是人工智能的一个分支，专注于使计算机能够理解、解释和生成人类语言。",
        status: "pending",
        confidence: 0.88,
      },
      {
        id: "5",
        question: "计算机视觉的应用有哪些？",
        answer:
          "计算机视觉广泛应用于图像识别、人脸识别、自动驾驶、医学影像分析、安防监控等领域。",
        status: "pending",
        confidence: 0.91,
      },
    ],
  },
];

export default function TextAnnotationWorkspace({
  onSaveAndNext,
  onSkipAndNext,
}: TextAnnotationWorkspaceProps) {
  const [selectedFile, setSelectedFile] = useState<FileData | null>(
    mockFiles[0]
  );
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedQAs, setSelectedQAs] = useState<string[]>([]);

  const handleFileSelect = (file: FileData) => {
    setSelectedFile(file);
    setSelectedQAs([]);
  };

  const handleQAStatusChange = (
    qaId: string,
    status: "approved" | "rejected"
  ) => {
    if (selectedFile) {
      const updatedFile = {
        ...selectedFile,
        qaPairs: selectedFile.qaPairs.map((qa) =>
          qa.id === qaId ? { ...qa, status } : qa
        ),
      };
      setSelectedFile(updatedFile);

      message({
        title: status === "approved" ? "已标记为留用" : "已标记为不留用",
        description: `QA对 "${qaId}" 状态已更新`,
      });
    }
  };

  const handleBatchApprove = () => {
    if (selectedFile && selectedQAs.length > 0) {
      const updatedFile = {
        ...selectedFile,
        qaPairs: selectedFile.qaPairs.map((qa) =>
          selectedQAs.includes(qa.id)
            ? { ...qa, status: "approved" as const }
            : qa
        ),
      };
      setSelectedFile(updatedFile);
      setSelectedQAs([]);

      message({
        title: "批量操作完成",
        description: `已将 ${selectedQAs.length} 个QA对标记为留用`,
      });
    }
  };

  const handleBatchReject = () => {
    if (selectedFile && selectedQAs.length > 0) {
      const updatedFile = {
        ...selectedFile,
        qaPairs: selectedFile.qaPairs.map((qa) =>
          selectedQAs.includes(qa.id)
            ? { ...qa, status: "rejected" as const }
            : qa
        ),
      };
      setSelectedFile(updatedFile);
      setSelectedQAs([]);

      message({
        title: "批量操作完成",
        description: `已将 ${selectedQAs.length} 个QA对标记为不留用`,
      });
    }
  };

  const handleQASelect = (qaId: string, checked: boolean) => {
    if (checked) {
      setSelectedQAs([...selectedQAs, qaId]);
    } else {
      setSelectedQAs(selectedQAs.filter((id) => id !== qaId));
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked && selectedFile) {
      setSelectedQAs(selectedFile.qaPairs.map((qa) => qa.id));
    } else {
      setSelectedQAs([]);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "approved":
        return <Badge className="bg-green-100 text-green-800">留用</Badge>;
      case "rejected":
        return <Badge className="bg-red-100 text-red-800">不留用</Badge>;
      default:
        return <Badge>待标注</Badge>;
    }
  };

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return "text-gray-500";
    if (confidence >= 0.8) return "text-green-600";
    if (confidence >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  const filteredQAs =
    selectedFile?.qaPairs.filter((qa) => {
      const matchesSearch =
        qa.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
        qa.answer.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus =
        statusFilter === "all" || qa.status === statusFilter;
      return matchesSearch && matchesStatus;
    }) || [];

  return (
    <div className="flex-1 flex">
      {/* File List */}
      <div className="w-80 border-r bg-gray-50 p-4">
        <div className="space-y-4">
          <div>
            <h3 className="font-medium mb-2">文件列表</h3>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input placeholder="搜索文件..." className="pl-10" />
            </div>
          </div>

          <div className="h-96">
            <div className="space-y-2">
              {mockFiles.map((file) => (
                <div
                  key={file.id}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    selectedFile?.id === file.id
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                  onClick={() => handleFileSelect(file)}
                >
                  <div className="flex items-center space-x-2">
                    <File className="w-4 h-4 text-gray-400" />
                    <div className="flex-1">
                      <div className="font-medium text-sm">{file.name}</div>
                      <div className="text-xs text-gray-500">
                        {file.qaPairs.length} 个QA对
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* QA Annotation Area */}
      <div className="flex-1 p-6">
        {selectedFile ? (
          <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold">{selectedFile.name}</h2>
                <p className="text-gray-500">
                  共 {selectedFile.qaPairs.length} 个QA对
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  onClick={onSaveAndNext}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  保存并下一个
                </Button>
                <Button onClick={onSkipAndNext}>跳过</Button>
              </div>
            </div>

            {/* Filters and Batch Actions */}
            <Card>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      placeholder="搜索QA对..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 w-64"
                    />
                  </div>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-3 py-2 border rounded-md text-sm"
                  >
                    <option value="all">全部状态</option>
                    <option value="pending">待标注</option>
                    <option value="approved">已留用</option>
                    <option value="rejected">不留用</option>
                  </select>
                </div>

                {selectedQAs.length > 0 && (
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">
                      已选择 {selectedQAs.length} 个
                    </span>
                    <Button
                      onClick={handleBatchApprove}
                      size="sm"
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <ThumbsUp className="w-4 h-4 mr-1" />
                      批量留用
                    </Button>
                    <Button
                      onClick={handleBatchReject}
                      size="sm"
                      variant="destructive"
                    >
                      <ThumbsDown className="w-4 h-4 mr-1" />
                      批量不留用
                    </Button>
                  </div>
                )}
              </div>
            </Card>

            {/* QA List */}
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <Checkbox
                  checked={
                    selectedQAs.length === filteredQAs.length &&
                    filteredQAs.length > 0
                  }
                  onChange={handleSelectAll}
                />
                <span className="text-sm font-medium">全选</span>
              </div>

              <div className="h-500">
                <div className="space-y-4">
                  {filteredQAs.map((qa) => (
                    <Card
                      key={qa.id}
                      className="hover:shadow-md transition-shadow"
                    >
                      <div className="space-y-3">
                        <div className="flex items-start justify-between">
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              checked={selectedQAs.includes(qa.id)}
                              onCheckedChange={(checked) =>
                                handleQASelect(qa.id, checked as boolean)
                              }
                            />
                            <MessageSquare className="w-4 h-4 text-blue-500" />
                            <span className="text-sm font-medium">
                              QA-{qa.id}
                            </span>
                          </div>
                          <div className="flex items-center space-x-2">
                            {qa.confidence && (
                              <span
                                className={`text-xs ${getConfidenceColor(
                                  qa.confidence
                                )}`}
                              >
                                置信度: {(qa.confidence * 100).toFixed(1)}%
                              </span>
                            )}
                            {getStatusBadge(qa.status)}
                          </div>
                        </div>

                        <div className="space-y-2">
                          <div>
                            <div className="flex items-center space-x-2 mb-1">
                              <HelpCircle className="w-4 h-4 text-blue-500" />
                              <span className="text-sm font-medium text-blue-700">
                                问题
                              </span>
                            </div>
                            <p className="text-sm bg-blue-50 p-3 rounded">
                              {qa.question}
                            </p>
                          </div>

                          <div>
                            <div className="flex items-center space-x-2 mb-1">
                              <MessageSquare className="w-4 h-4 text-green-500" />
                              <span className="text-sm font-medium text-green-700">
                                答案
                              </span>
                            </div>
                            <p className="text-sm bg-green-50 p-3 rounded">
                              {qa.answer}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center justify-end space-x-2">
                          <Button
                            onClick={() =>
                              handleQAStatusChange(qa.id, "approved")
                            }
                            size="sm"
                            variant={
                              qa.status === "approved" ? "default" : "outline"
                            }
                            className={
                              qa.status === "approved"
                                ? "bg-green-600 hover:bg-green-700"
                                : ""
                            }
                          >
                            <ThumbsUp className="w-4 h-4 mr-1" />
                            留用
                          </Button>
                          <Button
                            onClick={() =>
                              handleQAStatusChange(qa.id, "rejected")
                            }
                            size="sm"
                            variant={
                              qa.status === "rejected"
                                ? "destructive"
                                : "outline"
                            }
                          >
                            <ThumbsDown className="w-4 h-4 mr-1" />
                            不留用
                          </Button>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <File className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                选择文件开始标注
              </h3>
              <p className="text-gray-500">
                从左侧文件列表中选择一个文件开始标注工作
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
