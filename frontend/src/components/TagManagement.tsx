import React, { useEffect, useState } from "react";
import { Drawer, Input, Button, App } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { Edit, Save, TagIcon, X, Trash } from "lucide-react";
import { TagItem } from "@/pages/DataManagement/dataset.model";

interface CustomTagProps {
  isEditable?: boolean;
  tag: { id: number; name: string };
  editingTag?: string | null;
  editingTagValue?: string;
  setEditingTag?: React.Dispatch<React.SetStateAction<string | null>>;
  setEditingTagValue?: React.Dispatch<React.SetStateAction<string>>;
  handleEditTag?: (tag: { id: number; name: string }, value: string) => void;
  handleCancelEdit?: (tag: { id: number; name: string }) => void;
  handleDeleteTag?: (tag: { id: number; name: string }) => void;
}

function CustomTag({
  isEditable = false,
  tag,
  editingTag,
  editingTagValue,
  setEditingTag,
  setEditingTagValue,
  handleEditTag,
  handleCancelEdit,
  handleDeleteTag,
}: CustomTagProps) {
  return (
    <div
      key={tag.id}
      className="flex items-center justify-between px-4 py-2 border-card hover:bg-gray-50"
    >
      {editingTag?.id === tag.id ? (
        <div className="flex gap-2 flex-1">
          <Input
            value={editingTagValue}
            onChange={(e) => setEditingTagValue?.(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter") {
                handleEditTag?.(tag, editingTagValue);
              }
              if (e.key === "Escape") {
                setEditingTag?.(null);
                setEditingTagValue?.("");
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
            onClick={() => handleCancelEdit?.(tag)}
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
                  setEditingTag?.(tag);
                  setEditingTagValue?.(tag.name);
                }}
                icon={<Edit className="w-3 h-3" />}
              />
              <Button
                danger
                type="text"
                size="small"
                onClick={() => handleDeleteTag?.(tag)}
                icon={<Trash className="w-3 h-3" />}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}

const TagManager: React.FC = ({
  onFetch,
  onCreate,
  onDelete,
  onUpdate,
}: {
  onFetch: () => Promise<any>;
  onCreate: (tag: Pick<TagItem, "name">) => Promise<{ ok: boolean }>;
  onDelete: (tagId: number) => Promise<{ ok: boolean }>;
  onUpdate: (tag: TagItem) => Promise<{ ok: boolean }>;
}) => {
  const [showTagManager, setShowTagManager] = useState(false);
  const { message } = App.useApp();
  const [tags, setTags] = useState<{ id: number; name: string }[]>([]);
  const [newTag, setNewTag] = useState("");
  const [editingTag, setEditingTag] = useState<string | null>(null);
  const [editingTagValue, setEditingTagValue] = useState("");

  // 获取标签列表
  const fetchTags = async () => {
    if (!onFetch) return;
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
      await onCreate?.({
        name: tag,
      });
      fetchTags();
      message.success("标签添加成功");
    } catch (error) {
      message.error("添加标签失败");
    }
  };

  // 删除标签
  const deleteTag = async (tag: TagItem) => {
    try {
      await onDelete?.(tag.id);
      fetchTags();
      message.success("标签删除成功");
    } catch (error) {
      message.error("删除标签失败");
    }
  };

  const updateTag = async (oldTag: TagItem, newTag: string) => {
    try {
      await onUpdate?.({ ...oldTag, name: newTag });
      fetchTags();
      message.success("标签更新成功");
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

  const handleEditTag = (tag: TagItem, value: string) => {
    if (value.trim()) {
      updateTag(tag, value.trim());
      setEditingTag(null);
      setEditingTagValue("");
    }
  };

  const handleCancelEdit = (tag: string) => {
    setEditingTag(null);
    setEditingTagValue("");
  };

  const handleDeleteTag = (tag: TagItem) => {
    deleteTag(tag);
    setEditingTag(null);
    setEditingTagValue("");
  };

  useEffect(() => {
    if (showTagManager) fetchTags();
  }, [showTagManager]);

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
        width={500}
      >
        <div className="space-y-4 flex-overflow">
          {/* Add New Tag */}
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

          <div className="flex-overflow">
            <div className="overflow-auto grid grid-cols-2 gap-2">
              {tags.map((tag) => (
                <CustomTag
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
        </div>
      </Drawer>
    </>
  );
};

export default TagManager;
