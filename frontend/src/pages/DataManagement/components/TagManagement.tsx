import React, { useState } from "react";
import { Drawer, Input, Button, message } from "antd";
import { Plus, Edit, Save, Trash2, TagIcon, X } from "lucide-react";
import { useTagsOperation } from "../hooks/useTagsOperation";

const TagManager: React.FC = () => {
  const [messageApi] = message.useMessage();
  const {
    tags,
    newTag,
    setNewTag,
    handleEditTag,
    handleDeleteTag,
    updateTag,
    addTag,
    deleteTag,
    editingTag,
    setEditingTag,
    editingTagValue,
    setEditingTagValue,
    handleCreateNewTag,
  } = useTagsOperation(messageApi);
  const [showTagManager, setShowTagManager] = useState(false);
  const [availableTags, setAvailableTags] = useState<string[]>([]);

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
            <label>添加新标签</label>
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

          <div className="grid grid-cols-2 gap-2 mt-4">
            {tags.map((tag) => (
              <div
                key={tag}
                className="flex items-center justify-between px-2 border border-gray-100 rounded hover:bg-blue-50"
              >
                {editingTag === tag ? (
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
                    <span className="text-sm">{tag}</span>
                    <div className="flex gap-1">
                      <Button
                        onClick={() => {
                          setEditingTag(tag);
                          setEditingTagValue(tag);
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
