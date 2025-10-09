import React, { useState } from "react";
import { Drawer, Input, Button, Tag } from "antd";
import { Plus, Edit, Save, Trash2, TagIcon, X } from "lucide-react";
import { useTagsOperation } from "../../hooks/useTagsOperation";

const TagManager: React.FC = () => {
  const {
    tags,
    newTag,
    editingTag,
    editingTagValue,
    setNewTag,
    handleEditTag,
    updateTag,
    addTag,
    deleteTag,
    setEditingTag,
    setEditingTagValue,
    handleCreateNewTag,
  } = useTagsOperation();
  const [showTagManager, setShowTagManager] = useState(false);
  const [availableTags, setAvailableTags] = useState<string[]>([]);

  const preparedTags = [
    { id: "1", name: "重要" },
    { id: "2", name: "待处理" },
    { id: "3", name: "已完成" },
    { id: "4", name: "审核中" },
    { id: "5", name: "高优先级" },
    { id: "6", name: "低优先级" },
    { id: "7", name: "客户A" },
    { id: "8", name: "客户B" },
  ];

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
        <div className="space-y-4">
          {/* Add New Tag */}
          <div className="space-y-2">
            <div className="flex gap-2">
              <Input
                placeholder="输入标签名称..."
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === "Enter") {
                    addTag(e.target.value);
                  }
                }}
              />
              <Button
                type="primary"
                onClick={handleCreateNewTag}
                disabled={!newTag.trim()}
              >
                <Plus className="w-4 h-4 mr-2" />
                添加
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-2">
            <h3 className="font-medium">预置标签</h3>
            {preparedTags.length > 0 &&
              preparedTags.map((tag) => (
                <Tag key={tag.id} color="blue" className="m-1 cursor-pointer">
                  {tag.name}
                </Tag>
              ))}
          </div>

          <div className="grid grid-cols-2 gap-2 mt-4">
            {tags.map((tag) => (
              <div
                key={tag.id}
                className="flex items-center justify-between px-2 border border-gray-100 rounded hover:bg-blue-50"
              >
                {editingTag === tag.id ? (
                  <div className="flex items-center gap-2 flex-1">
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
                      type="link"
                      icon={<Save className="w-3 h-3" />}
                      onClick={() => updateTag(tag, editingTagValue)}
                    ></Button>
                    <Button
                      type="link"
                      icon={<X className="w-3 h-3" />}
                      onClick={() => setEditingTag(null)}
                    ></Button>
                  </div>
                ) : (
                  <>
                    <span className="text-sm">{tag.name}</span>
                    <div className="flex gap-1">
                      <Button
                        onClick={() => {
                          setEditingTag(tag.id);
                          setEditingTagValue(tag.name);
                        }}
                        type="text"
                        icon={<Edit className="w-3 h-3" />}
                      ></Button>
                      <Button
                        type="text"
                        icon={<Trash2 className="w-3 h-3" />}
                        onClick={() => deleteTag(tag)}
                      ></Button>
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
