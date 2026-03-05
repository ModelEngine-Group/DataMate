import React, { useEffect, useState } from "react";
import { Drawer, Input, Button, App } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { Edit, Save, TagIcon, X, Trash } from "lucide-react";
import { TagItem } from "@/pages/DataManagement/dataset.model";
import { useTranslation } from "react-i18next";

interface CustomTagProps {
  isEditable?: boolean;
  tag: TagItem;
  editingTag?: TagItem | null;
  editingTagValue?: string;
  setEditingTag?: React.Dispatch<React.SetStateAction<TagItem | null>>;
  setEditingTagValue?: React.Dispatch<React.SetStateAction<string>>;
  handleEditTag?: (tag: TagItem, value: string) => void;
  handleCancelEdit?: (tag: TagItem) => void;
  handleDeleteTag?: (tag: TagItem) => void;
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
  onFetch: (params?: any) => Promise<{ data: TagItem[] }>;
  onCreate: (tag: Pick<TagItem, "name">) => Promise<{ data: TagItem }>;
  onDelete: (ids: string) => Promise<any>;
  onUpdate: (tag: TagItem) => Promise<{ data: TagItem }>;
}) => {
  const [showTagManager, setShowTagManager] = useState(false);
  const { message } = App.useApp();
  const { t } = useTranslation();
  const [tags, setTags] = useState<TagItem[]>([]);
  const [newTag, setNewTag] = useState("");
  const [editingTag, setEditingTag] = useState<TagItem | null>(null);
  const [editingTagValue, setEditingTagValue] = useState("");

  // 获取标签列表
  const fetchTags = async () => {
    if (!onFetch) return;
    try {
      const { data } = await onFetch?.();
      setTags(data || []);
    } catch (e) {
      // 错误已由全局拦截器处理，无需重复提示
      console.error("Failed to fetch tags:", e);
    }
  };

  // 添加标签
  const addTag = async (tag: string) => {
    try {
      await onCreate?.({
        name: tag,
      });
      fetchTags();
      setNewTag("");
      message.success(t("tagManagement.messages.addSuccess"));
    } catch (error) {
      // 错误已由全局拦截器处理，无需重复提示
      console.error("Failed to add tag:", error);
    }
  };

  // 删除标签
  const deleteTag = async (tag: TagItem) => {
    try {
      await onDelete?.(tag.id);
      fetchTags();
      message.success(t("tagManagement.messages.deleteSuccess"));
    } catch (error) {
      // 错误已由全局拦截器处理，无需重复提示
      console.error("Failed to delete tag:", error);
    }
  };

  const updateTag = async (oldTag: TagItem, newTag: string) => {
    try {
      await onUpdate?.({ ...oldTag, name: newTag });
      fetchTags();
      message.success(t("tagManagement.messages.updateSuccess"));
    } catch (error) {
      // 错误已由全局拦截器处理，无需重复提示
      console.error("Failed to update tag:", error);
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

  const handleCancelEdit = (tag: TagItem) => {
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
        {t("tagManagement.manageTags")}
      </Button>
      <Drawer
        open={showTagManager}
        onClose={() => setShowTagManager(false)}
        title={t("tagManagement.manageTags")}
        width={500}
      >
        <div className="space-y-4 flex-overflow">
          {/* Add New Tag */}
          <div className="flex gap-2">
            <Input
              placeholder={t("tagManagement.tagNamePlaceholder")}
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
              {t("tagManagement.createTag")}
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
