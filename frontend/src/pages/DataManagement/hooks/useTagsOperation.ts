import { mockTags } from "@/mock/dataset";
import { useState } from "react";

export function useTagsOperation(message) {
  // 标签相关状态
  const [tags, setTags] = useState<string[]>(mockTags);
  const [newTag, setNewTag] = useState("");
  const [editingTag, setEditingTag] = useState<string | null>(null);
  const [editingTagValue, setEditingTagValue] = useState("");
  const [showAddTagPopover, setShowAddTagPopover] = useState(false);
  const [showDetailAddTagPopover, setShowDetailAddTagPopover] = useState(false);
  const [detailNewTag, setDetailNewTag] = useState("");

  // 获取标签列表
  const fetchTags = async () => {
    try {
      const response = await fetch(`/api/tags`);
      const data = await response.json();
      setTags(data);
    } catch (e) {
      message.error("获取标签失败");
    }
  };

  // 添加标签
  const addTag = async (tag: string) => {
    try {
      const response = await fetch(`/api/tags`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ tag }),
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
      const response = await fetch(`/api/tags/${tag}`, {
        method: "DELETE",
      });
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
      const response = await fetch(`/api/tags/${oldTag}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ tag: newTag }),
      });
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
      updateTag(tag, value.trim());
      setEditingTag(null);
      setEditingTagValue("");
    }
  };

  const handleDeleteTag = (tag: string) => {
    deleteTag(tag);
    setEditingTag(null);
    setEditingTagValue("");
  };

  return {
    tags,
    newTag,
    setNewTag,
    handleCreateNewTag,
    handleEditTag,
    handleDeleteTag,
    editingTag,
    setEditingTag,
    editingTagValue,
    setEditingTagValue,
    showAddTagPopover,
    setShowAddTagPopover,
    fetchTags,
    addTag,
    deleteTag,
    updateTag,
  };
}
