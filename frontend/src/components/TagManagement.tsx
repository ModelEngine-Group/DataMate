import React, { useEffect, useState } from "react";
import { Drawer, Input, Button, App } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { Edit, Save, TagIcon, X, Trash } from "lucide-react";
import { TagItem } from "@/pages/DataManagement/dataset.model";

function Tag({
  isEditable,
  tag,
  editingTag,
  editingTagValue,
  setEditingTag,
  setEditingTagValue,
  handleEditTag,
  handleCancelEdit,
  handleDeleteTag,
}) {
  return (
    <div
      key={tag.id}
      className="flex items-center justify-between px-4 py-2 border border-gray-100 rounded-md hover:bg-gray-50"
    >
      {editingTag?.id === tag.id ? (
        <div className="flex gap-2 flex-1">
          <Input
            value={editingTagValue}
            onChange={(e) => setEditingTagValue(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter") {
                handleEditTag(tag.name, editingTagValue);
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
            type="link"
            size="small"
            icon={<Save className="w-3 h-3" />}
          />
          <Button
            danger
            type="text"
            size="small"
            onClick={() => handleCancelEdit(tag)}
            icon={<X className="w-3 h-3" />}
          />
        </div>
      ) : (
        <>
          <span className="text-sm">{tag.name}</span>
          {isEditable && (
            <div className="flex gap-1">
              <Button
                size="small"
                type="text"
                onClick={() => {
                  setEditingTag(tag);
                  setEditingTagValue(tag.name);
                }}
                icon={<Edit className="w-3 h-3" />}
              />
              <Button
                danger
                type="text"
                size="small"
                onClick={() => handleDeleteTag(tag)}
                icon={<Trash className="w-3 h-3" />}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}

export const mockPreparedTags = [
  { id: "1", name: "重要" },
  { id: "2", name: "待处理" },
  { id: "3", name: "已完成" },
  { id: "4", name: "审核中" },
  { id: "5", name: "高优先级" },
  { id: "6", name: "低优先级" },
  { id: "7", name: "客户A" },
  { id: "8", name: "客户B" },
];

const TagManager: React.FC = ({
  onFetch,
  onCreate,
  onDelete,
  onUpdate,
}: {
  onFetch: () => Promise<any>;
  onCreate: (tag: TagItem) => Promise<{ ok: boolean }>;
  onDelete: (tagId: number) => Promise<{ ok: boolean }>;
  onUpdate: (oldTagId: number, newTag: string) => Promise<{ ok: boolean }>;
}) => {
  const [showTagManager, setShowTagManager] = useState(false);
  const { message } = App.useApp();
  const [tags, setTags] = useState<{ id: number; name: string }[]>([]);
  const [newTag, setNewTag] = useState("");
  const [editingTag, setEditingTag] = useState<string | null>(null);
  const [editingTagValue, setEditingTagValue] = useState("");

  // 预置标签
  const [preparedTags, setPreparedTags] = useState(mockPreparedTags);

  // 获取标签列表
  const fetchTags = async () => {
    try {
      const { data } = await onFetch?.();
      setTags(data || []);
    } catch (e) {
      message.error("获取标签失败");
    }
  };

  // 添加标签
  const addTag = async (tag: string) => {
    try {
      const response = await onCreate?.({
        name: tag,
        color: "#111111",
        description: "23",
      });
      if (response.ok) {
        fetchTags();
        message.success("标签添加成功");
      } else {
        message.error("添加标签失败");
      }
    } catch (error) {
      message.error("添加标签失败");
    }
  };

  // 删除标签
  const deleteTag = async (tag: string) => {
    try {
      const response = await onDelete?.(tag.id);
      if (response.ok) {
        fetchTags();
        message.success("标签删除成功");
      } else {
        message.error("删除标签失败");
      }
    } catch (error) {
      message.error("删除标签失败");
    }
  };

  const updateTag = async (oldTag: string, newTag: string) => {
    try {
      const response = await onUpdate?.(oldTag.id, newTag);
      if (response.ok) {
        fetchTags();
        message.success("标签更新成功");
      } else {
        message.error("更新标签失败");
      }
    } catch (error) {
      message.error("更新标签失败");
    }
  };

  const handleCreateNewTag = () => {
    if (newTag.trim()) {
      addTag(newTag.trim());
      setNewTag("");
    }
  };

  const handleEditTag = (tag: string, value: string) => {
    if (value.trim()) {
      updateTag(tag.id, value.trim());
      setEditingTag(null);
      setEditingTagValue("");
    }
  };

  const handleCancelEdit = (tag: string) => {
    setEditingTag(null);
    setEditingTagValue("");
  };

  const handleDeleteTag = (tag: string) => {
    deleteTag(tag.id);
    setEditingTag(null);
    setEditingTagValue("");
  };

  useEffect(() => {
    fetchTags();
  }, []);

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
                allowClear
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
                icon={<PlusOutlined />}
              >
                添加
              </Button>
            </div>
          </div>

          <h2 className="font-large font-bold w-full">预置标签</h2>
          <div className="grid grid-cols-2 gap-2">
            {preparedTags.length > 0 &&
              preparedTags.map((tag) => (
                <Tag
                  key={tag.id}
                  tag={tag}
                  editingTag={editingTag}
                  editingTagValue={editingTagValue}
                  setEditingTag={setEditingTag}
                  setEditingTagValue={setEditingTagValue}
                  handleEditTag={handleEditTag}
                  handleCancelEdit={handleCancelEdit}
                  handleDeleteTag={handleDeleteTag}
                />
              ))}
          </div>

          <h2 className="font-large font-bold w-full">自定义标签</h2>
          <div className="grid grid-cols-2 gap-2 mt-4">
            {tags.map((tag) => (
              <Tag
                isEditable
                key={tag.id}
                tag={tag}
                editingTag={editingTag}
                editingTagValue={editingTagValue}
                setEditingTag={setEditingTag}
                setEditingTagValue={setEditingTagValue}
                handleEditTag={handleEditTag}
                handleCancelEdit={handleCancelEdit}
                handleDeleteTag={handleDeleteTag}
              />
            ))}
          </div>
        </div>
      </Drawer>
    </>
  );
};

export default TagManager;
