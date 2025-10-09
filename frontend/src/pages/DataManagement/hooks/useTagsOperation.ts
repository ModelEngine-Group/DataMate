import { useEffect, useState } from "react";
import {
  createDatasetTagUsingPost,
  deleteDatasetTagByIdUsingDelete,
  queryDatasetTagsUsingGet,
  updateDatasetTagByIdUsingPut,
} from "../dataset.api";
import { App } from "antd";

export function useTagsOperation() {
  // 标签相关状态
  const { message } = App.useApp();
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState("");
  const [editingTag, setEditingTag] = useState<string | null>(null);
  const [editingTagValue, setEditingTagValue] = useState("");
  const [showAddTagPopover, setShowAddTagPopover] = useState(false);
  const [showDetailAddTagPopover, setShowDetailAddTagPopover] = useState(false);
  const [detailNewTag, setDetailNewTag] = useState("");

  // 获取标签列表
  const fetchTags = async () => {
    try {
      const { data } = await queryDatasetTagsUsingGet();
      setTags(data || []);
    } catch (e) {
      message.error("获取标签失败");
    }
  };

  // 添加标签
  const addTag = async (tag: string) => {
    try {
      const response = await createDatasetTagUsingPost(tag);
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
      const response = await deleteDatasetTagByIdUsingDelete(tag.id);
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
      const response = await updateDatasetTagByIdUsingPut(oldTag.id, newTag);
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

  const handleDeleteTag = (tag: string) => {
    deleteTag(tag.id);
    setEditingTag(null);
    setEditingTagValue("");
  };

  useEffect(() => {
    fetchTags();
  }, []);

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
