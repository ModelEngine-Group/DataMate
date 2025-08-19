"use client";

import type React from "react";

import { useState } from "react";

import {
  Plus,
  Settings,
  Edit,
  File,
  Trash2,
  ArrowLeft,
  Save,
} from "lucide-react";

const KnowledgeBaseDetailPage: React.FC = () => {
  const [editForm, setEditForm] = useState<KnowledgeBase | null>(null);
  const [showEditFileDialog, setShowEditFileDialog] = useState<File | null>(
    null
  );
  const [currentView, setCurrentView] = useState<"detail" | "edit">("detail");
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">编辑知识库</h1>
          <p className="text-gray-600 mt-1">修改知识库配置和文件</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => router.push("/knowledge-generation/detail/1")}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="space-y-6">
            <div className="space-y-4">
              <h4 className="font-medium">基本信息</h4>
              <div className="space-y-3">
                <div>
                  <Label htmlFor="edit-kb-name">知识库名称</Label>
                  <Input
                    id="edit-kb-name"
                    value={editForm.name}
                    onChange={(e) =>
                      setEditForm({ ...editForm, name: e.target.value })
                    }
                  />
                </div>
                <div>
                  <Label htmlFor="edit-kb-description">描述</Label>
                  <Textarea
                    id="edit-kb-description"
                    value={editForm.description}
                    onChange={(e) =>
                      setEditForm({ ...editForm, description: e.target.value })
                    }
                    rows={3}
                  />
                </div>
              </div>
            </div>

            <Separator />

            <div className="space-y-4">
              <h4 className="font-medium flex items-center gap-2">
                <Settings className="w-4 h-4" />
                配置设置
              </h4>
              <div className="space-y-3">
                <div>
                  <Label>嵌入模型</Label>
                  <Select
                    value={editForm.config.embeddingModel}
                    onValueChange={(value) =>
                      setEditForm({
                        ...editForm,
                        config: { ...editForm.config, embeddingModel: value },
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="text-embedding-3-large">
                        text-embedding-3-large
                      </SelectItem>
                      <SelectItem value="text-embedding-3-small">
                        text-embedding-3-small
                      </SelectItem>
                      <SelectItem value="text-embedding-ada-002">
                        text-embedding-ada-002
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>向量数据库</Label>
                  <Select
                    value={editForm.vectorDatabase}
                    onValueChange={(value) =>
                      setEditForm({ ...editForm, vectorDatabase: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {vectorDatabases.map((db) => (
                        <SelectItem key={db.id} value={db.id}>
                          {db.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>分块大小</Label>
                    <Input
                      type="number"
                      value={editForm.config.chunkSize}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          config: {
                            ...editForm.config,
                            chunkSize: Number(e.target.value),
                          },
                        })
                      }
                    />
                  </div>
                  <div>
                    <Label>重叠长度</Label>
                    <Input
                      type="number"
                      value={editForm.config.overlap}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          config: {
                            ...editForm.config,
                            overlap: Number(e.target.value),
                          },
                        })
                      }
                    />
                  </div>
                </div>
              </div>
            </div>

            <Separator />

            <div className="space-y-4">
              <h4 className="font-medium flex items-center gap-2">
                <File className="w-4 h-4" />
                文件管理
              </h4>
              <div className="space-y-3">
                {editForm.files.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <File className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="font-medium">{file.name}</p>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <span>{file.size}</span>
                          <Badge variant="outline" className="text-xs">
                            {file.source === "upload"
                              ? "上传文件"
                              : "数据集文件"}
                          </Badge>
                          {file.source === "dataset" && (
                            <Badge variant="outline" className="text-xs">
                              数据集: {file.datasetId}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowEditFileDialog(file)}
                      >
                        <Edit className="w-4 h-4 mr-1" />
                        编辑
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteFile(file)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
                <Button variant="outline" className="w-full bg-transparent">
                  <Plus className="w-4 h-4 mr-2" />
                  添加文件
                </Button>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button onClick={handleEditKB} className="flex-1">
                <Save className="w-4 h-4 mr-2" />
                保存更改
              </Button>
              <Button
                variant="outline"
                onClick={() => setCurrentView("detail")}
              >
                取消
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
