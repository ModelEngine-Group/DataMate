"use client";

import React, { useState } from "react";
import { Drawer, Input, Button } from "antd";
import { Plus, Edit, Save, Trash2, TagIcon } from "lucide-react";
import { useDatasets } from "../hooks/useDatasets";

const TagManager: React.FC = () => {
  const { fetchDatasets } = useDatasets();
  const [showTagManager, setShowTagManager] = useState(false);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [tagCategories] = useState<Record<string, string[]>>({
    医学专科: ["病理", "心内科", "呼吸科", "药学", "手术"],
    数据类型: ["WSI", "文献", "心音", "呼吸音", "视频", "多模态"],
    疾病类型: ["肺癌", "心脏病", "肺部疾病", "呼吸系统疾病"],
    任务类型: ["分类", "检测", "分割", "信息抽取", "步骤识别", "技能评估"],
    技术标签: ["NLP", "音频分类", "视频分析", "多模态融合"],
  });

  const [newTag, setNewTag] = useState("");
  const [editingTag, setEditingTag] = useState<string | null>(null);
  const [editingTagValue, setEditingTagValue] = useState("");

  const handleCreateNewTag = () => {
    if (newTag.trim() && !availableTags.includes(newTag.trim())) {
      setAvailableTags([...availableTags, newTag.trim()]);
      setNewTag("");
      setShowAddTagPopover(false);
    }
  };

  const handleEditTag = (oldTag: string, newTag: string) => {
    if (newTag.trim() && newTag !== oldTag) {
      // 更新可用标签列表
      setAvailableTags(
        availableTags.map((tag) => (tag === oldTag ? newTag.trim() : tag))
      );
      fetchDatasets?.();
      setEditingTag(null);
      setEditingTagValue("");
    }
  };

  const handleDeleteTag = (tagToDelete: string) => {
    // 从可用标签中删除
    setAvailableTags(availableTags.filter((tag) => tag !== tagToDelete));
    // 从所有数据集中删除该标签
    fetchDatasets?.();
  };

  return (
    <>
      <Button
        icon={<TagIcon className="w-4 h-4 mr-2" />}
        onClick={() => setShowTagManager(true)}
      >
        标签管理
      </Button>
      <Drawer
        open={showTagManager}
        onClose={() => setShowTagManager(false)}
        title="标签管理"
      >
        <div className="space-y-6 mt-6">
          {/* Add New Tag */}
          <div className="space-y-2">
            <label>添加新标签</label>
            <div className="flex gap-2">
              <Input
                placeholder="输入标签名称..."
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === "Enter") {
                    handleCreateNewTag();
                  }
                }}
              />
              <Button onClick={handleCreateNewTag} disabled={!newTag.trim()}>
                <Plus className="w-4 h-4 mr-2" />
                添加
              </Button>
            </div>
          </div>

          {/* Tag Categories */}
          {Object.entries(tagCategories).map(([category, categoryTags]) => (
            <div key={category} className="space-y-2">
              <div className="grid grid-cols-2 gap-2 ">
                {categoryTags
                  .filter((tag) => availableTags.includes(tag))
                  .map((tag) => (
                    <div
                      key={tag}
                      className="flex items-center justify-between p-2 border rounded-lg hover:bg-gray-50"
                    >
                      {editingTag === tag ? (
                        <div className="flex gap-2 flex-1">
                          <Input
                            value={editingTagValue}
                            onChange={(e) => setEditingTagValue(e.target.value)}
                            onKeyPress={(e) => {
                              if (e.key === "Enter") {
                                handleEditTag(tag, editingTagValue);
                              }
                              if (e.key === "Escape") {
                                setEditingTag(null);
                                setEditingTagValue("");
                              }
                            }}
                            className="h-6 text-sm"
                            autoFocus
                          />
                          <Button
                            onClick={() => handleEditTag(tag, editingTagValue)}
                            className="h-6 w-6 p-0"
                          >
                            <Save className="w-3 h-3" />
                          </Button>
                        </div>
                      ) : (
                        <>
                          <span className="text-sm">{tag}</span>
                          <div className="flex gap-1">
                            <Button
                              onClick={() => {
                                setEditingTag(tag);
                                setEditingTagValue(tag);
                              }}
                              className="h-6 w-6 p-0"
                            >
                              <Edit className="w-3 h-3" />
                            </Button>
                            <Button
                              onClick={() => handleDeleteTag(tag)}
                              className="h-6 w-6 p-0 text-red-500 hover:text-red-700"
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
              </div>
            </div>
          ))}

          <div className="grid grid-cols-2 gap-2 ">
            {availableTags
              .filter(
                (tag) => !Object.values(tagCategories).flat().includes(tag)
              )
              .map((tag) => (
                <div
                  key={tag}
                  className="flex items-center justify-between p-2 border rounded-lg hover:bg-gray-50"
                >
                  {editingTag === tag ? (
                    <div className="flex gap-2 flex-1">
                      <Input
                        value={editingTagValue}
                        onChange={(e) => setEditingTagValue(e.target.value)}
                        onKeyPress={(e) => {
                          if (e.key === "Enter") {
                            handleEditTag(tag, editingTagValue);
                          }
                          if (e.key === "Escape") {
                            setEditingTag(null);
                            setEditingTagValue("");
                          }
                        }}
                        className="h-6 text-sm"
                        autoFocus
                      />
                      <Button
                        onClick={() => handleEditTag(tag, editingTagValue)}
                        className="h-6 w-6 p-0"
                      >
                        <Save className="w-3 h-3" />
                      </Button>
                    </div>
                  ) : (
                    <>
                      <span className="text-sm">{tag}</span>
                      <div className="flex gap-1">
                        <Button
                          onClick={() => {
                            setEditingTag(tag);
                            setEditingTagValue(tag);
                          }}
                          className="h-6 w-6 p-0"
                        >
                          <Edit className="w-3 h-3" />
                        </Button>
                        <Button
                          onClick={() => handleDeleteTag(tag)}
                          className="h-6 w-6 p-0 text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </>
                  )}
                </div>
              ))}
          </div>
        </div>
      </Drawer>
    </>
  );
};

export default TagManager;
