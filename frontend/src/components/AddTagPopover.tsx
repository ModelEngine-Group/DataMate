import { Button, Input, Popover, theme, Tag, Empty } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { useEffect, useMemo, useState } from "react";

interface Tag {
  id: number;
  name: string;
  color: string;
}

interface AddTagPopoverProps {
  tags: Tag[];
  onFetchTags?: () => Promise<Tag[]>;
  onAddTag?: (tag: Tag) => void;
  onCreateAndTag?: (tagName: string) => void;
}

export default function AddTagPopover({
  tags,
  onFetchTags,
  onAddTag,
  onCreateAndTag,
}: AddTagPopoverProps) {
  const { token } = theme.useToken();
  const [showPopover, setShowPopover] = useState(false);

  const [newTag, setNewTag] = useState("");
  const [allTags, setAllTags] = useState<Tag[]>([]);

  const tagsSet = useMemo(() => new Set(tags.map((tag) => tag.id)), [tags]);

  const fetchTags = async () => {
    if (onFetchTags && showPopover) {
      const data = await onFetchTags?.();
      setAllTags(data || []);
    }
  };
  useEffect(() => {
    fetchTags();
  }, [showPopover]);

  const availableTags = useMemo(() => {
    return allTags.filter((tag) => !tagsSet.has(tag.id));
  }, [allTags, tagsSet]);

  const handleCreateAndAddTag = () => {
    if (newTag.trim()) {
      onCreateAndTag?.(newTag.trim());
      setNewTag("");
    }

    setShowPopover(false);
  };

  const tagPlusStyle: React.CSSProperties = {
    height: 22,
    background: token.colorBgContainer,
    borderStyle: "dashed",
  };

  return (
    <>
      <Popover
        open={showPopover}
        trigger="click"
        placement="bottom"
        onOpenChange={setShowPopover}
        content={
          <div className="space-y-4 w-[300px]">
            <h4 className="font-medium border-b pb-2 border-gray-100">
              添加标签
            </h4>
            {/* Available Tags */}
            {availableTags?.length ? (
              <div className="space-y-2">
                <h5 className="text-sm">选择现有标签</h5>
                <div className="max-h-32 overflow-y-auto space-y-1">
                  {availableTags.map((tag) => (
                    <span
                      key={tag.id}
                      className="h-7 w-full justify-start text-xs cursor-pointer flex items-center px-2 rounded hover:bg-gray-100"
                      onClick={() => {
                        onAddTag?.(tag.name);
                        setShowPopover(false);
                      }}
                    >
                      <PlusOutlined className="w-3 h-3 mr-1" />
                      {tag.name}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <Empty description="没有可用标签，请先创建标签。" />
            )}

            {/* Create New Tag */}
            <div className="space-y-2 border-t border-gray-100 pt-3">
              <h5 className="text-sm">创建新标签</h5>
              <div className="flex gap-2">
                <Input
                  placeholder="输入新标签名称..."
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  className="h-8 text-sm"
                />
                <Button
                  onClick={() => handleCreateAndAddTag()}
                  disabled={!newTag.trim()}
                  type="primary"
                >
                  添加
                </Button>
              </div>
            </div>

            <Button block onClick={() => setShowPopover(false)}>
              取消
            </Button>
          </div>
        }
      >
        <Tag
          style={tagPlusStyle}
          icon={<PlusOutlined />}
          className="cursor-pointer"
          onClick={() => setShowPopover(true)}
        >
          添加标签
        </Tag>
      </Popover>
    </>
  );
}
