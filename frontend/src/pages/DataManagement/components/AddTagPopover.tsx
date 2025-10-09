import { Button, Input, Popover } from "antd";
import { Tag } from "antd";
import { Plus, Save } from "lucide-react";
import { useEffect, useState } from "react";

export default function AddTagPopover({ tags }) {
  const [availableTags, setAvailableTags] = useState<string[]>([
    "重要",
    "待处理",
    "已完成",
    "审核中",
    "高优先级",
    "低优先级",
    "客户A",
    "客户B",
  ]);
  const [newTag, setNewTag] = useState("");

  const fetchAvailableTags = () => {
    // Fetch available tags from backend or use predefined tags
    setAvailableTags([
      "重要",
      "待处理",
      "已完成",
      "审核中",
      "高优先级",
      "低优先级",
      "客户A",
      "客户B",
    ]);
  };

  useEffect(() => {
    fetchAvailableTags();
  }, []);

  const handleAddTag = (datasetId: number, tag: string) => {
    setDatasets(
      datasets.map((dataset) =>
        dataset.id === datasetId && !dataset.tags.includes(tag)
          ? { ...dataset, tags: [...dataset.tags, tag] }
          : dataset
      )
    );
    // Update selected dataset if it's currently selected
    if (selectedDataset && selectedDataset.id === datasetId) {
      setSelectedDataset({
        ...selectedDataset,
        tags: selectedDataset.tags.includes(tag)
          ? selectedDataset.tags
          : [...selectedDataset.tags, tag],
      });
    }
  };

  const handleCreateAndAddTag = (datasetId: number) => {
    if (newTag.trim() && !availableTags.includes(newTag.trim())) {
      setAvailableTags([...availableTags, newTag.trim()]);
    }
    if (newTag.trim()) {
      handleAddTag(datasetId, newTag.trim());
      setNewTag("");
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2 items-center">
        {tags.map((tag, tagIndex) => (
          <Tag key={tagIndex} className="text-xs">
            {tag}
          </Tag>
        ))}
        <Popover
          trigger="click"
          placement="bottom"
          content={
            <div className="w-[300px]">
              <h4 className="font-medium">添加标签</h4>

              {/* Available Tags */}
              <div className="space-y-2">
                <label className="text-sm">选择现有标签</label>
                <div className="max-h-32 overflow-y-auto space-y-1">
                  {availableTags
                    .filter((tag) => !tags.includes(tag))
                    .map((tag) => (
                      <Button
                        key={tag}
                        className="h-7 w-full justify-start text-xs"
                        onClick={() => onAdd(tag)}
                      >
                        <Plus className="w-3 h-3 mr-1" />
                        {tag}
                      </Button>
                    ))}
                </div>
              </div>

              {/* Create New Tag */}
              <div className="space-y-2 border-t pt-3">
                <label className="text-sm">创建新标签</label>
                <div className="flex gap-2">
                  <Input
                    placeholder="输入新标签名称..."
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === "Enter") {
                        handleCreateAndAddTag(dataset.id);
                      }
                    }}
                    className="h-8 text-sm"
                  />
                  <Button
                    onClick={() => handleCreateAndAddTag()}
                    disabled={!detailNewTag.trim()}
                    className="h-8"
                  >
                    添加
                  </Button>
                </div>
              </div>
            </div>
          }
        >
          <Button className="h-6 text-xs bg-transparent border-dashed">
            <Plus className="w-3 h-3 mr-1" />
            添加标签
          </Button>
        </Popover>
      </div>
    </div>
  );
}
