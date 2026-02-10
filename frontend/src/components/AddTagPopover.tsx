import { Button, Input, Popover, theme, Tag, Empty } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

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
  const { t } = useTranslation();
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
              {t("tagManagement.addTag")}
            </h4>
            {/* Available Tags */}
            {availableTags?.length ? (
              <div className="space-y-2">
                <h5 className="text-sm">{t("tagManagement.selectExistingTags")}</h5>
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
              <Empty description={t("tagManagement.noAvailableTags")} />
            )}

            {/* Create New Tag */}
            <div className="space-y-2 border-t border-gray-100 pt-3">
              <h5 className="text-sm">{t("tagManagement.createNewTag")}</h5>
              <div className="flex gap-2">
                <Input
                  placeholder={t("tagManagement.newTagNamePlaceholder")}
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  className="h-8 text-sm"
                />
                <Button
                  onClick={() => handleCreateAndAddTag()}
                  disabled={!newTag.trim()}
                  type="primary"
                >
                  {t("tagManagement.createTag")}
                </Button>
              </div>
            </div>

            <Button block onClick={() => setShowPopover(false)}>
              {t("tagManagement.cancel")}
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
          {t("tagManagement.addTag")}
        </Tag>
      </Popover>
    </>
  );
}
